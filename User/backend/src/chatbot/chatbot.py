"""Main chatbot module for handling conversations."""
import logging
import re
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.document.processor import chunk_text, extract_text_from_pdf, extract_text_from_image
from src.document.attachments import get_attachments_for_session, get_attachment_file

logger = logging.getLogger(__name__)

# Max chunks to embed at once (avoids OOM on large PDFs)
MAX_DOC_CHUNKS_TO_EMBED = 50


class AluminiumChatBot:
    """Main chatbot class for handling aluminum product queries and uploaded documents."""

    def __init__(
        self,
        retriever,
        embeddings_manager,
        config,
        history_collection=None,
        database=None,
        attachments_collection_name: Optional[str] = None,
    ):
        """
        Initialize the Chatbot.

        Args:
            retriever: Retriever instance for finding relevant products
            embeddings_manager: EmbeddingsManager instance
            config: Configuration object
            history_collection: Optional MongoDB collection for persisting history
            database: Optional MongoDB database for loading session attachments
            attachments_collection_name: Name of the collection storing attachment metadata
        """
        self.retriever = retriever
        self.embeddings_manager = embeddings_manager
        self.config = config
        self.conversation_history = []
        self.history_collection = history_collection
        self.database = database
        self.attachments_collection_name = attachments_collection_name or "chat_attachments"
        self.system_prompt = self._create_system_prompt()

    def _build_message(
        self,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict:
        """Create a message payload with timestamp."""
        msg = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
        }
        if user_id:
            msg['user_id'] = user_id
        return msg

    def _generate_session_id(self) -> str:
        """Generate a unique chat session id."""
        return f"chat_{uuid.uuid4().hex}"

    def _save_message(self, message: Dict):
        """Persist message to in-memory history and MongoDB when enabled."""
        self.conversation_history.append(message)

        if self.history_collection is not None:
            try:
                self.history_collection.insert_one(message)
            except Exception as exc:  # fail soft to keep chat flowing
                logger.error(f"Failed to write message to MongoDB: {exc}")
    
    def _create_system_prompt(self) -> str:
        """
        Create system prompt for the chatbot.
        """
        return """You are a helpful assistant. You do two things:

1) WHEN THE USER ASKS ABOUT AN UPLOADED DOCUMENT (e.g. summarize, explain, what does it say):
   - Answer ONLY from the document content provided. Do not assume the document is about aluminum or any specific topic.
   - If the document is NOT about aluminum products, say so clearly and summarize what the document is actually about (e.g. "This document is about ...").
   - If the document IS about aluminum/jobs/quotations, you can use that and also refer to product/job data when the user asks for budget or quotation.
   - Be accurate, concise, and faithful to the document. Do not invent content or force aluminum into the answer when the document is about something else.

2) WHEN THE USER ASKS ABOUT ALUMINUM PRODUCTS OR JOBS (without a document, or explicitly about products):
   - Use the product/job knowledge base to answer: specifications, applications, prices, quotations, jobs (AAW).
   - Be accurate and reference specific details when provided.

Always: Understand what the user is asking. Prefer the document content when they are asking about the uploaded file. Be honest if you don't have the information."""

    def _get_config_value(self, key: str, default=None):
        """Get config value from object or mapping."""
        if hasattr(self.config, "get"):
            return self.config.get(key, default)
        return getattr(self.config, key, default)

    def _normalize_text(self, text: str) -> str:
        """Normalize text for intent checks."""
        normalized = re.sub(r"[\?\!\.,]+", " ", text.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized.replace("aluminium", "aluminum")

    def _is_smalltalk(self, text: str) -> bool:
        """Detect casual smalltalk queries."""
        greetings = {"hi", "hello", "hey", "hiya", "good morning", "good afternoon", "good evening"}
        smalltalk_keywords = {
            "how are you", "who are you", "what can you do", "help", "can you help",
            "thanks", "thank you", "bye", "goodbye", "see you", "nice to meet you",
        }
        if any(greet == text or text.startswith(greet + " ") for greet in greetings):
            return True
        return any(k in text for k in smalltalk_keywords)

    def _is_random_chat_request(self, text: str) -> bool:
        """Detect requests for random chat or a random topic."""
        random_keywords = {
            "random", "chat", "talk", "anything", "surprise me", "whatever",
            "just chatting", "let's chat", "casual",
        }
        return any(k in text for k in random_keywords)

    def _build_smalltalk_response(self, text: str) -> str:
        """Return a friendly smalltalk response."""
        if "how are you" in text:
            return "I'm doing well—ready to help. Ask me anything about aluminum products or materials." \
                   " If you'd like, I can also suggest a random product."
        if any(k in text for k in ["bye", "goodbye", "see you"]):
            return "Goodbye! If you have more questions about aluminum products, just ask anytime."
        if any(k in text for k in ["thanks", "thank you"]):
            return "You're welcome! Want details on a specific aluminum alloy or application?"
        if any(k in text for k in ["who are you", "what can you do", "help"]):
            return (
                "I'm your aluminum products chatbot. I can answer product questions, compare alloys, "
                "suggest applications, and show prices/specs. You can also ask for a random product."
            )
        return "Hello! I’m here to help. Ask about aluminum products, or say 'random' for a surprise pick."

    def _build_random_product_response(self) -> Optional[str]:
        """Return a response featuring a random product."""
        try:
            df = getattr(self.retriever, "dataframe", None)
            if df is None or len(df) == 0:
                return None
            product = df.sample(1).iloc[0].to_dict()
            return (
                "Here’s a random aluminum product suggestion:\n\n"
                f"- **{product.get('product_name', 'N/A')}**\n"
                f"  Category: {product.get('category', 'N/A')}\n"
                f"  Price: ${product.get('price', 'N/A')}\n"
                f"  Applications: {product.get('applications', 'N/A')}\n\n"
                "Ask for more details or another random pick."
            )
        except Exception as exc:
            logger.error(f"Failed to pick random product: {exc}")
            return None

    def _is_list_products_request(self, text: str) -> bool:
        """Detect requests to list or show products."""
        triggers = {
            "list products",
            "show products",
            "all products",
            "available products",
            "what products",
            "what are the products",
            "what are the aluminum products",
            "what are aluminum products",
        }
        if any(t in text for t in triggers):
            return True
        return "products" in text or "product list" in text

    def _is_document_summary_request(self, text: str) -> bool:
        """True if user is asking to summarize/explain the attached document (with or without saying 'pdf')."""
        summary_keywords = {
            "summarize", "summarise", "summerize", "summary", "summery", "key points", "key point",
            "main points", "main point", "high level", "overview", "short version", "brief",
            "what does it say", "what is this", "what is the document", "explain this",
            "explain the document", "tell me about", "whats in", "what's in", "content of",
            "budget", "budget plan", "cost estimate", "quotation", "quote",
            "place job", "place order", "create job", "create quotation", "read", "read this", "read it"
        }
        doc_keywords = {
            "attached pdf", "attached document", "this pdf", "this document",
            "uploaded pdf", "uploaded document", "the pdf", "the document",
            "the file", "this file", "file", "document",
        }
        is_summary = any(k in text for k in summary_keywords)
        about_doc = any(k in text for k in doc_keywords)
        # "summarize" or "explain" alone (when we have a doc) = document request
        return is_summary and (about_doc or len(text.split()) <= 6)

    def _wants_document_answer(self, text: str) -> bool:
        """True when the user's question is clearly about document content (summarize, explain, what does it say)."""
        triggers = (
            "summarize", "summarise", "summerize", "summary", "key points", "main points", "overview",
            "brief", "what does it say", "what is this", "explain this", "explain the",
            "tell me about", "whats in", "what's in", "content of", "what is the document",
            "read", "read this", "read it"
        )
        return any(t in text for t in triggers)

    def _build_product_list_response(self, limit: int = 10) -> str:
        """Return a readable list of products."""
        df = getattr(self.retriever, "dataframe", None)
        if df is None or len(df) == 0:
            return "I don’t have any products loaded right now. Please check the data source."

        subset = df.head(limit)
        lines = []
        for _, row in subset.iterrows():
            name = row.get("product_name", "N/A")
            category = row.get("category", "N/A")
            lines.append(f"- {name} ({category})")

        remaining = len(df) - len(subset)
        suffix = f"\n\nThere are {remaining} more products. Ask for a category or say 'show more'." if remaining > 0 else ""

        return "Here are some aluminum products:\n\n" + "\n".join(lines) + suffix
    
    def _get_document_context_for_session(self, session_id: Optional[str], query: str) -> str:
        """
        Load attachments for the session, chunk extracted text, and return relevant chunks for the query.
        """
        if not session_id or self.database is None or not self.attachments_collection_name:
            logger.debug("Document context skipped: session_id=%s, db=%s", bool(session_id), self.database is not None)
            return ""

        try:
            attachments = get_attachments_for_session(
                self.database,
                self.attachments_collection_name,
                session_id,
            )
        except Exception as e:
            logger.warning("Failed to load attachments for session %s: %s", session_id, e)
            return ""

        if not attachments:
            logger.info("No attachments found for session %s", session_id)
            return ""

        logger.info("Document context: session %s has %d attachment(s)", session_id, len(attachments))
        all_chunks = []
        for att in attachments:
            try:
                text = (att.get("extracted_text") or "").strip()
                # If text was not extracted at upload (e.g. extraction failed), try lazily now.
                if not text:
                    file_bytes = get_attachment_file(self.database, att)
                    if file_bytes:
                        ctype = (att.get("content_type") or "").lower()
                        if ctype == "application/pdf":
                            timeout = self._get_config_value("DOC_PDF_TIMEOUT", 30)
                            max_pages = self._get_config_value("DOC_MAX_PAGES", 80)
                            text = extract_text_from_pdf(
                                file_bytes,
                                att.get("filename") or "",
                                timeout=timeout,
                                max_pages=max_pages,
                            ) or ""
                        elif ctype.startswith("image/"):
                            text = extract_text_from_image(file_bytes, att.get("filename") or "") or ""
                        if text:
                            try:
                                self.database[self.attachments_collection_name].update_one(
                                    {"_id": att["_id"]},
                                    {"$set": {"extracted_text": text[:1_000_000]}},
                                )
                            except Exception as exc:
                                logger.warning("Failed to update extracted_text for attachment %s: %s", att.get("_id"), exc)
                    else:
                        logger.warning("Could not read file for attachment %s (filename=%s)", att.get("_id"), att.get("filename"))
                if not text:
                    continue
                chunk_size = self._get_config_value("DOC_CHUNK_SIZE", 500)
                overlap = self._get_config_value("DOC_CHUNK_OVERLAP", 50)
                chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
                filename = att.get("filename", "document")
                for c in chunks:
                    all_chunks.append({"text": c, "filename": filename})
            except Exception as exc:
                import traceback
                traceback.print_exc()
                logger.warning("Skipping attachment %s (%s): %s", att.get("_id"), att.get("filename"), exc)

        if not all_chunks:
            logger.info("No text chunks from attachments for session %s (extraction may have produced no text)", session_id)
            return ""

        top_k_doc = min(self._get_config_value("TOP_K_DOC_CHUNKS", 12), len(all_chunks))
        chunks_to_use = all_chunks
        if len(all_chunks) > MAX_DOC_CHUNKS_TO_EMBED:
            step = max(1, len(all_chunks) // MAX_DOC_CHUNKS_TO_EMBED)
            indices = list(range(0, len(all_chunks), step))[:MAX_DOC_CHUNKS_TO_EMBED]
            chunks_to_use = [all_chunks[i] for i in indices]

        try:
            q = (query or "").strip() or "summary"
            query_embedding = self.embeddings_manager.encode_text(q)
            if query_embedding is None:
                selected = chunks_to_use[:top_k_doc]
            else:
                chunk_texts = [c["text"] for c in chunks_to_use]
                # Use manager to encode instead of model directly, routing through Ollama if configured
                chunk_embeddings = self.embeddings_manager.create_embeddings(chunk_texts)
                
                if chunk_embeddings is None:
                    selected = chunks_to_use[:top_k_doc]
                else:
                    sims = cosine_similarity([query_embedding], chunk_embeddings)[0]
                    top_k_here = min(top_k_doc, len(chunks_to_use))
                    top_indices = np.argsort(sims)[::-1][:top_k_here]
                    selected = [chunks_to_use[i] for i in top_indices]
        except Exception as e:
            logger.warning("PDF chunk ranking failed (using first chunks): %s", e)
            selected = chunks_to_use[:top_k_doc]

        return self._format_document_context(selected)

    def _format_document_context(self, chunks: List[Dict[str, str]]) -> str:
        """Format retrieved document chunks for the response."""
        if not chunks:
            return ""
        lines = ["CONTENT FROM UPLOADED FILES (use this to answer questions about the attached documents):"]
        for i, item in enumerate(chunks, 1):
            lines.append(f"\n[{item.get('filename', 'document')} - excerpt {i}]:\n{item.get('text', '')}")
        return "\n".join(lines)

    def _format_products_context(self, products: List[Dict]) -> str:
        """
        Format retrieved products into context for the response.
        
        Args:
            products (List[Dict]): Retrieved products
            
        Returns:
            str: Formatted product information
        """
        if not products:
            return ""
        
        context = "RELEVANT PRODUCTS:\n"
        for i, product in enumerate(products, 1):
            context += f"\n{i}. {product.get('product_name', 'N/A')}\n"
            context += f"   Category: {product.get('category', 'N/A')}\n"
            context += f"   Price: ${product.get('price', 'N/A')}\n"
            context += f"   Description: {product.get('description', 'N/A')}\n"
            context += f"   Specifications: {product.get('specifications', 'N/A')}\n"
            context += f"   Applications: {product.get('applications', 'N/A')}\n"
            if 'similarity_score' in product:
                context += f"   Relevance Score: {product['similarity_score']:.2f}\n"
        
        return context
    
    def _build_llm_messages(
        self,
        query: str,
        products_context: str,
        document_context: str,
        document_only: bool = False,
    ) -> List[Dict[str, str]]:
        """Build messages for the LLM. document_only=True: answer only from document; do not assume aluminum."""
        context_parts = []
        if document_context:
            context_parts.append(document_context.strip())
        if products_context and not document_only:
            context_parts.append(products_context.strip())
        context_block = "\n\n".join(context_parts).strip()

        user_content = f"Question: {query.strip()}"
        if context_block:
            if document_only:
                user_content += (
                    "\n\nDocument content (from the user's uploaded file):\n"
                    f"{context_block}\n\n"
                    "Instructions: Answer ONLY from this document. Do not assume the document is about aluminum. "
                    "If the document is not about aluminum products, say so clearly and summarize what it is actually about. "
                    "Be accurate and concise."
                )
            else:
                user_content += (
                    "\n\nContext (uploaded documents and/or product catalog):\n"
                    f"{context_block}\n\n"
                    "Use this context to answer. If the document is not about aluminum, do not force aluminum into the answer. "
                    "If something is not covered, say you don't have that information."
                )
        return [{"role": "user", "content": user_content}]

    def _create_response(
        self,
        query: str,
        context: str,
        document_context: str = "",
    ) -> str:
        """
        Create a response based on query, retrieved products, and optional document context.

        When document context is present and USE_OLLAMA_FOR_DOCUMENTS is True, tries Ollama first
        for stronger document QA. Otherwise uses LOCAL_LLM (transformers) or template fallback.
        """
        document_only = bool(document_context and not context.strip())
        messages = self._build_llm_messages(
            query, context, document_context, document_only=document_only
        )
        use_ollama_for_docs = getattr(self.config, "USE_OLLAMA_FOR_DOCUMENTS", False)
        ollama_base = getattr(self.config, "OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = getattr(self.config, "OLLAMA_MODEL", "llama3.2")

        # When we have document context, prefer Ollama for better PDF/document understanding.
        doc_max_tokens = getattr(self.config, "DOC_LLM_MAX_TOKENS", 1024)
        if document_context and use_ollama_for_docs:
            try:
                from src.chatbot.ollama_llm import generate_answer_with_ollama, is_ollama_available
                if is_ollama_available(ollama_base):
                    answer = generate_answer_with_ollama(
                        system_prompt=self.system_prompt,
                        messages=messages,
                        base_url=ollama_base,
                        model=ollama_model,
                        max_tokens=doc_max_tokens,
                        temperature=getattr(self.config, "LOCAL_LLM_TEMPERATURE", 0.2),
                    )
                    if answer:
                        return answer
            except Exception as ollama_err:
                logger.warning("Ollama document response failed, trying local LLM: %s", ollama_err)

        # Prefer real-time answer generation with Ollama OR local LLM
        if use_ollama_for_docs and is_ollama_available(ollama_base):
            try:
                answer = generate_answer_with_ollama(
                    system_prompt=self.system_prompt,
                    messages=messages,
                    base_url=ollama_base,
                    model=ollama_model,
                    max_tokens=doc_max_tokens,
                    temperature=getattr(self.config, "LOCAL_LLM_TEMPERATURE", 0.2),
                )
                if answer:
                    return answer
            except Exception as ollama_fall_err:
                logger.warning("Ollama regular response failed: %s", ollama_fall_err)
        
        elif getattr(self.config, "LOCAL_LLM_ENABLED", False):
            try:
                from src.chatbot.local_llm import generate_answer
                default_tokens = getattr(self.config, "LOCAL_LLM_MAX_NEW_TOKENS", 256)
                max_tokens = doc_max_tokens if document_context else default_tokens
                answer = generate_answer(
                    system_prompt=self.system_prompt,
                    messages=messages,
                    model_name=getattr(self.config, "LOCAL_LLM_MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct"),
                    device=getattr(self.config, "LOCAL_LLM_DEVICE", "auto"),
                    max_new_tokens=max_tokens,
                    temperature=getattr(self.config, "LOCAL_LLM_TEMPERATURE", 0.2),
                )
                if answer:
                    return answer
            except Exception as llm_err:
                logger.warning("Local LLM generation failed, falling back to simple template: %s", llm_err)

        # Fallback: echo context when LLM is unavailable.
        if document_context:
            if document_only:
                return (
                    "I've read your document. Here is the content I have:\n\n"
                    f"{document_context[:4000]}{'...' if len(document_context) > 4000 else ''}\n\n"
                    "Ask me to summarize or explain any part, or about budget/quotation if it applies."
                )
            intro = "I've read your document."
            if context.strip():
                intro = "I've read your document and matched relevant jobs/products."
            return f"""{intro}\n\nDocument:\n{document_context[:3000]}{'...' if len(document_context) > 3000 else ''}\n\nRelated products:\n{context}\n\nAsk follow-up questions (summarize, budget, quotation)."""

        # No document context – answer from retrieved jobs/products only.
        base = f"Question: {query.strip()}\n\n"
        if context.strip():
            base += f"Relevant jobs/products:\n{context}\n\n"
        else:
            base += "I don't have matching products for that. Ask about alloys, categories, or applications.\n\n"
        base += "You can also upload a PDF and ask me to summarize it."
        return base

    def _create_fallback_response(self, query: str) -> str:
        """Fallback response when no products are matched."""
        random_hint = self._build_random_product_response()
        random_part = f"\n\nHere’s something to consider:\n{random_hint}" if random_hint else ""
        return (
            "I didn’t catch a specific aluminum product in that question. "
            "Tell me an alloy (6061, 7075), category (aerospace, marine), or application (aircraft, construction), "
            "and I’ll recommend options. If you just want to chat, say so."
            + random_part + f"\n\nYou asked: {query}"
        )
    
    def chat(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict:
        """
        Process a user message and return a response.
        
        Args:
            user_message (str): User's message
            
        Returns:
            Dict: Response containing answer and retrieved products
        """
        try:
            session_id = session_id or self._generate_session_id()
            normalized = self._normalize_text(user_message)
            if self._is_smalltalk(normalized):
                response_text = self._build_smalltalk_response(normalized)
                self._save_message(self._build_message('user', user_message, session_id, user_id))
                self._save_message(self._build_message('assistant', response_text, session_id, user_id))
                return {
                    'success': True,
                    'message': response_text,
                    'retrieved_products': [],
                    'products_count': 0,
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                }

            if self._is_random_chat_request(normalized):
                response_text = self._build_random_product_response() or (
                    "I can chat about aluminum products. Ask for a specific alloy, "
                    "or tell me an application like aerospace or marine."
                )
                self._save_message(self._build_message('user', user_message, session_id, user_id))
                self._save_message(self._build_message('assistant', response_text, session_id, user_id))
                return {
                    'success': True,
                    'message': response_text,
                    'retrieved_products': [],
                    'products_count': 0,
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                }

            if self._is_list_products_request(normalized):
                response_text = self._build_product_list_response()
                self._save_message(self._build_message('user', user_message, session_id, user_id))
                self._save_message(self._build_message('assistant', response_text, session_id, user_id))
                return {
                    'success': True,
                    'message': response_text,
                    'retrieved_products': [],
                    'products_count': 0,
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                }

            self._save_message(self._build_message('user', user_message, session_id, user_id))

            # Retrieve relevant document chunks from uploaded PDFs/images for this session
            document_context = ""
            try:
                document_context = self._get_document_context_for_session(session_id, user_message) or ""
            except Exception as doc_err:
                logger.exception("Document context failed (continuing without): %s", doc_err)

            has_doc = bool(document_context)
            is_product_explicit = any(k in normalized for k in ["product", "aluminum", "aluminium", "alloy", "price", "cost", "specifications", "applications"])
            
            # Document-first: If we have an uploaded document, assume ALL questions are about the document
            # UNLESS the user explicitly asks about aluminum products.
            is_doc_summary = self._is_document_summary_request(normalized) or (
                has_doc and self._wants_document_answer(normalized)
            ) or (has_doc and not is_product_explicit)

            # Retrieve products only when the question is not purely about the document
            products = []
            context = ""
            if not is_doc_summary:
                products = self.retriever.retrieve(user_message)
                if not products:
                    products = self.retriever.retrieve_by_keywords(user_message)
                context = self._format_products_context(products)

            # Decide how to build the response
            try:
                if is_doc_summary:
                    if document_context:
                        # User asked to summarize/describe the attached PDF: answer only from the document,
                        # do not show the RELEVANT PRODUCTS block.
                        response_text = self._create_response(user_message, "", document_context=document_context)
                        products = []
                    else:
                        # No document context: extraction + OCR (if enabled) produced no text.
                        response_text = (
                            "I couldn't read any text from that file. Try uploading a PDF with selectable text, "
                            "or a clearer image. If it's a scanned PDF, installing Tesseract and poppler may help. "
                            "Once I can read it, I'll summarize it and answer questions about its content."
                        )
                else:
                    if document_context:
                        # Has document: answer from it (and products only if relevant); don't force aluminum
                        response_text = self._create_response(
                            user_message, context or "", document_context=document_context
                        )
                    elif not products or not context:
                        response_text = self._create_fallback_response(user_message)
                    else:
                        response_text = self._create_response(user_message, context)
            except Exception as resp_err:
                logger.warning("Create response failed: %s", resp_err)
                response_text = (
                    "I had trouble formatting that answer. Your document (if any) may still be available. "
                    "Try asking again with a bit more detail, or re-upload the PDF."
                )

            # Add bot response to history
            self._save_message(self._build_message('assistant', response_text, session_id, user_id))
            
            # Trim in-memory history if too long
            max_history = self._get_config_value("MAX_CHAT_HISTORY", 10)
            if len(self.conversation_history) > max_history:
                self.conversation_history = self.conversation_history[-max_history:]
            
            logger.info(f"Processed query: {user_message[:50]}...")
            
            return {
                'success': True,
                'message': response_text,
                'retrieved_products': products,
                'products_count': len(products),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.exception("Error processing chat")
            err_msg = str(e) or type(e).__name__
            return {
                'success': False,
                'message': f'Sorry, I encountered an error processing your request. Please try again. ({err_msg})',
                'error': err_msg,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_history(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get conversation history, optionally filtered by session_id and/or user_id.

        Returns:
            List[Dict]: Conversation history
        """
        if self.history_collection is None:
            subset = self.conversation_history
            if session_id:
                subset = [m for m in subset if m.get('session_id') == session_id]
            if user_id:
                subset = [m for m in subset if m.get('user_id') == user_id]
            return subset

        try:
            query = {}
            if session_id:
                query['session_id'] = session_id
            if user_id:
                query['user_id'] = user_id
            cursor = self.history_collection.find(query).sort("timestamp", 1)
            return [
                {
                    'role': doc.get('role'),
                    'content': doc.get('content'),
                    'timestamp': doc.get('timestamp'),
                    'session_id': doc.get('session_id'),
                    'user_id': doc.get('user_id'),
                }
                for doc in cursor
            ]
        except Exception as exc:
            logger.error(f"Failed to read history from MongoDB: {exc}")
            subset = self.conversation_history
            if session_id:
                subset = [m for m in subset if m.get('session_id') == session_id]
            if user_id:
                subset = [m for m in subset if m.get('user_id') == user_id]
            return subset

    def get_sessions(self, user_id: Optional[str] = None) -> List[Dict]:
        """Return a list of chat sessions with metadata, optionally for one user."""
        history = self.get_history(user_id=user_id)
        sessions = {}
        for msg in history:
            sid = msg.get('session_id') or 'default'
            sessions.setdefault(sid, []).append(msg)

        result = []
        for sid, msgs in sessions.items():
            msgs_sorted = sorted(msgs, key=lambda x: x.get('timestamp', ''))
            first_user = next((m for m in msgs_sorted if m.get('role') == 'user'), None)
            title = (first_user.get('content') if first_user else 'Conversation')
            result.append({
                'session_id': sid,
                'title': title[:80] if title else 'Conversation',
                'started_at': msgs_sorted[0].get('timestamp') if msgs_sorted else None,
                'last_message_at': msgs_sorted[-1].get('timestamp') if msgs_sorted else None,
                'message_count': len(msgs_sorted),
            })

        return sorted(result, key=lambda x: x.get('last_message_at') or '', reverse=True)

    def delete_session(self, session_id: str) -> int:
        """Delete a session's messages. Returns number deleted."""
        if not session_id:
            return 0

        if self.history_collection is None:
            before = len(self.conversation_history)
            self.conversation_history = [msg for msg in self.conversation_history if msg.get('session_id') != session_id]
            return before - len(self.conversation_history)

        try:
            result = self.history_collection.delete_many({'session_id': session_id})
            return result.deleted_count
        except Exception as exc:
            logger.error(f"Failed to delete session in MongoDB: {exc}")
            return 0
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

        if self.history_collection is not None:
            try:
                self.history_collection.delete_many({})
            except Exception as exc:
                logger.error(f"Failed to clear history in MongoDB: {exc}")
                return

        logger.info("Conversation history cleared")
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt.
        
        Returns:
            str: System prompt
        """
        return self.system_prompt
    
    def get_stats(self) -> Dict:
        """
        Get chatbot statistics.
        
        Returns:
            Dict: Statistics
        """
        if self.history_collection is not None:
            try:
                total_messages = self.history_collection.count_documents({})
                user_messages = self.history_collection.count_documents({'role': 'user'})
                assistant_messages = self.history_collection.count_documents({'role': 'assistant'})
            except Exception as exc:
                logger.error(f"Failed to read stats from MongoDB: {exc}")
                total_messages = len(self.conversation_history)
                user_messages = sum(1 for msg in self.conversation_history if msg['role'] == 'user')
                assistant_messages = sum(1 for msg in self.conversation_history if msg['role'] == 'assistant')
        else:
            total_messages = len(self.conversation_history)
            user_messages = sum(1 for msg in self.conversation_history if msg['role'] == 'user')
            assistant_messages = sum(1 for msg in self.conversation_history if msg['role'] == 'assistant')

        return {
            'total_messages': total_messages,
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'model_name': self.embeddings_manager.model_name,
            'embedding_dimension': self.embeddings_manager.get_embedding_dimension()
        }
