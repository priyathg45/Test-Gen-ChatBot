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
        
        # In-memory cache for Global Knowledge Base to speed up retrieval
        self.global_knowledge_cache = None
        self.global_knowledge_embeddings = None
        self.last_knowledge_refresh = None

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
        """Create a direct, flexible system prompt for the chatbot."""
        return """You are AAW Assistant — the premium, official AI for Active Aluminium Windows.
Your goal is to provide specific, accurate, and helpful answers using the provided context.

## RESPONSE STYLE
- **Direct & Specific**: Answer the user's question directly. If the context has specific details (IDs, specs, prices), include them.
- **Context-First**: Always prioritize the provided "CONTEXT" block. If the answer is there, use it.
- **Premium Layout**: 
    - Use Markdown **Tables** for comparing items or listing specifications.
    - **Bold** key technical terms (e.g., **6063-T5**), product names, and prices.
    - Use bullet points for any list of 3+ items.
- **No Fluff**: Avoid long introductory sentences. Get straight to the point.

## SOURCE CITATION
- ALWAYS state your source if using documents: **📄 Source: Page [X] of [Filename]**
- Mention the **🌐 Global Knowledge Base** if it was your source.
- End your response with: **📌 Information provided by AAW Product Intelligence.**

If you cannot find the answer in the context, say exactly: "I don't have enough specific information in the current documents to answer that accurately."
"""

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
        Load text from all attachments in this session and return relevant chunks with caching.
        """
        if not session_id or self.database is None or not self.attachments_collection_name:
            return ""

        try:
            attachments = get_attachments_for_session(
                self.database,
                self.attachments_collection_name,
                session_id,
            )
            if not attachments:
                if session_id in self.session_doc_cache:
                    del self.session_doc_cache[session_id]
                return ""

            # Check if cache is valid (based on attachment IDs)
            current_att_ids = sorted([str(a["_id"]) for a in attachments])
            cache_entry = self.session_doc_cache.get(session_id)
            
            needs_refresh = (
                not cache_entry or 
                cache_entry.get("att_ids") != current_att_ids
            )

            if needs_refresh:
                logger.info("Building document cache for session %s...", session_id)
                all_chunks = []
                for att in attachments:
                    try:
                        text = (att.get("extracted_text") or "").strip()
                        if not text:
                            file_bytes = get_attachment_file(self.database, att)
                            if file_bytes:
                                ctype = (att.get("content_type") or "").lower()
                                if ctype == "application/pdf":
                                    text = extract_text_from_pdf(
                                        file_bytes, att.get("filename", ""),
                                        timeout=self._get_config_value("DOC_PDF_TIMEOUT", 30),
                                        max_pages=self._get_config_value("DOC_MAX_PAGES", 80)
                                    ) or ""
                                elif ctype.startswith("image/"):
                                    text = extract_text_from_image(file_bytes, att.get("filename", "")) or ""
                                
                                if text:
                                    self.database[self.attachments_collection_name].update_one(
                                        {"_id": att["_id"]},
                                        {"$set": {"extracted_text": text[:1_000_000]}}
                                    )
                        
                        if text:
                            chunks = chunk_text(
                                text, 
                                chunk_size=self._get_config_value("DOC_CHUNK_SIZE", 500),
                                overlap=self._get_config_value("DOC_CHUNK_OVERLAP", 50)
                            )
                            filename = att.get("filename", "document")
                            for c in chunks:
                                all_chunks.append({"text": c, "filename": filename})
                    except Exception as exc:
                        logger.warning("Skipping attachment %s: %s", att.get("_id"), exc)

                if not all_chunks:
                    self.session_doc_cache[session_id] = {"chunks": [], "embeddings": None, "att_ids": current_att_ids}
                    return ""

                # Limit and embed
                chunks_to_use = all_chunks[:MAX_DOC_CHUNKS_TO_EMBED]
                chunk_texts = [c["text"] for c in chunks_to_use]
                logger.info("Creating embeddings for %d session chunks...", len(chunk_texts))
                embeddings = self.embeddings_manager.create_embeddings(chunk_texts)
                
                self.session_doc_cache[session_id] = {
                    "chunks": chunks_to_use,
                    "embeddings": embeddings,
                    "att_ids": current_att_ids
                }

            # Use cached data for ranking
            cache_entry = self.session_doc_cache[session_id]
            chunks_to_use = cache_entry["chunks"]
            chunk_embeddings = cache_entry["embeddings"]

            if not chunks_to_use:
                return ""

            top_k_doc = min(self._get_config_value("TOP_K_DOC_CHUNKS", 12), len(chunks_to_use))
            try:
                q = (query or "").strip() or "summary"
                query_embedding = self.embeddings_manager.encode_text(q)
                if query_embedding is None or chunk_embeddings is None:
                    selected = chunks_to_use[:top_k_doc]
                else:
                    sims = cosine_similarity([query_embedding], chunk_embeddings)[0]
                    top_k_here = min(top_k_doc, len(chunks_to_use))
                    top_indices = np.argsort(sims)[::-1][:top_k_here]
                    selected = [chunks_to_use[i] for i in top_indices if sims[top_indices[i]] > 0.15]
                    if not selected and len(top_indices) > 0:
                        selected = [chunks_to_use[top_indices[0]]]
            except Exception as e:
                logger.warning("Session doc ranking failed: %s", e)
                selected = chunks_to_use[:top_k_doc]

            return self._format_document_context(selected)

        except Exception as e:
            logger.error("Failed to load session documents: %s", e)
            return ""

    def _get_global_knowledge_context(self, query: str) -> str:
        """
        Load chunks from the global knowledge_base collection and return relevant ones for the query.
        Uses in-memory caching to avoid expensive re-embedding on every chat message.
        """
        knowledge_coll_name = getattr(self.config, "MONGO_KNOWLEDGE_COLLECTION", "knowledge_base")
        if self.database is None or not knowledge_coll_name:
            return ""

        try:
            coll = self.database[knowledge_coll_name]
            
            # Check if we need to refresh the cache (very basic check: count documents)
            current_count = coll.count_documents({})
            if current_count == 0:
                self.global_knowledge_cache = []
                self.global_knowledge_embeddings = None
                return ""

            needs_refresh = (
                self.global_knowledge_cache is None or 
                len(self.global_knowledge_cache) != current_count or
                (self.last_knowledge_refresh and (datetime.now() - self.last_knowledge_refresh).total_seconds() > 300)
            )

            if needs_refresh:
                logger.info("Refreshing Global Knowledge Cache (Count: %d)...", current_count)
                cursor = coll.find().limit(500)
                new_chunks = []
                for doc in cursor:
                    new_chunks.append({
                        "text": doc.get("content", ""),
                        "filename": doc.get("filename", "global_doc")
                    })
                
                self.global_knowledge_cache = new_chunks
                self.last_knowledge_refresh = datetime.now()
                
                # Pre-calculate embeddings for the cache
                if new_chunks:
                    chunk_texts = [c["text"] for c in new_chunks]
                    logger.info("Pre-calculating embeddings for %d global chunks...", len(chunk_texts))
                    self.global_knowledge_embeddings = self.embeddings_manager.create_embeddings(chunk_texts)
                else:
                    self.global_knowledge_embeddings = None

            if not self.global_knowledge_cache:
                return ""

            all_chunks = self.global_knowledge_cache
            chunk_embeddings = self.global_knowledge_embeddings
            top_k = min(self._get_config_value("TOP_K_KNOWLEDGE_CHUNKS", 4), len(all_chunks))
            
            # 1. Semantic Search
            selected_semantic_indices = []
            try:
                query_embedding = self.embeddings_manager.encode_text(query or "general information")
                if query_embedding is not None and chunk_embeddings is not None:
                    sims = cosine_similarity([query_embedding], chunk_embeddings)[0]
                    threshold = self._get_config_value("SIMILARITY_THRESHOLD", 0.6)
                    selected_semantic_indices = [i for i in np.argsort(sims)[::-1] if sims[i] >= threshold]
            except Exception as e:
                logger.warning("Knowledge ranking failed: %s", e)

            # 2. Keyword Search (Mirroring free-chatbot-main)
            selected_keyword_indices = []
            if self._get_config_value("ENABLE_KEYWORD_SEARCH", True) and query:
                import re as _re
                # Clean query and split into words
                q_clean = _re.sub(r'[^a-z0-9 ]', '', (query or "").lower())
                keywords = [w for w in q_clean.split() if len(w) > 2]
                if keywords:
                    for i, chunk in enumerate(all_chunks):
                        content = chunk.get("text", "").lower()
                        if any(kw in content for kw in keywords):
                            selected_keyword_indices.append(i)

            # Combine and remove duplicates, maintaining order (semantic first, then keyword)
            combined_indices = []
            seen = set()
            for idx in selected_semantic_indices:
                if idx not in seen:
                    combined_indices.append(idx)
                    seen.add(idx)
            for idx in selected_keyword_indices:
                if idx not in seen:
                    combined_indices.append(idx)
                    seen.add(idx)

            # Limit to top_k
            final_indices = combined_indices[:top_k]
            selected = [all_chunks[i] for i in final_indices]

            # 3. Recent Fallback (Mirroring free-chatbot-main)
            if not selected and self._get_config_value("ENABLE_RECENT_KNOWLEDGE_FALLBACK", True):
                logger.info("No specific matches found. Using recent knowledge fallback.")
                try:
                    sorted_chunks = sorted(all_chunks, key=lambda x: x.get('created_at', datetime.min), reverse=True)
                    selected = sorted_chunks[:2]
                except Exception:
                    selected = all_chunks[-2:]

            if not selected:
                return ""

            logger.info("Retrieved %d relevant chunks from global knowledge base (Semantic: %s, Keyword: %s).", 
                        len(selected), len(selected_semantic_indices[:top_k]), len(selected_keyword_indices[:top_k]))
            
            formatted = self._format_document_context(selected)
            # Tag it as global knowledge so LLM knows
            if formatted:
                return formatted.replace("=== DOCUMENT CONTEXT", "=== GLOBAL KNOWLEDGE BASE")
            return ""

        except Exception as e:
            logger.error("Failed to load global knowledge: %s", e)
            return ""

    def _detect_page_request(self, query: str) -> Optional[int]:
        """Return the 1-based page number if the user asked about a specific page, else None."""
        import re as _re
        patterns = [
            r"page\s+(\d+)",
            r"(\d+)(?:st|nd|rd|th)?\s+page",
            r"pg\.?\s*(\d+)",
        ]
        q = (query or "").strip().lower()
        for pat in patterns:
            m = _re.search(pat, q)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    pass
        return None

    def _format_document_context(self, chunks: List[Dict[str, str]]) -> str:
        """Format retrieved document chunks for the LLM with clear page section labels."""
        import re as _re
        if not chunks:
            return ""

        # Group chunks by (filename, page_num) to produce clean sections
        from collections import OrderedDict
        sections: OrderedDict = OrderedDict()
        for item in chunks:
            text = item.get("text", "")
            filename = item.get("filename", "document")
            m = _re.match(r"\[PAGE_(\d+)\]\n?", text)
            page_num = int(m.group(1)) if m else 0
            clean_text = _re.sub(r"^\[PAGE_\d+\]\n?", "", text).strip()
            key = (filename, page_num)
            if key not in sections:
                sections[key] = []
            sections[key].append(clean_text)

        lines = ["=== DOCUMENT CONTEXT (extracted from uploaded file) ===\n"]
        for (filename, page_num), texts in sections.items():
            page_label = f"Page {page_num}" if page_num else "Unknown page"
            lines.append(f"--- {page_label} of '{filename}' ---")
            lines.append("\n".join(t for t in texts if t))
            lines.append("")  # blank line between sections

        lines.append("=== END OF DOCUMENT CONTEXT ===")
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
        requested_page: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """Build messages for the LLM. document_only=True: answer only from document."""
        import re as _re

        context_parts = []
        if document_context:
            context_parts.append(document_context.strip())
        if products_context and not document_only:
            context_parts.append(products_context.strip())
        context_block = "\n\n".join(context_parts).strip()

        # Try to extract filename from context header
        file_match = _re.search(r"--- [^\[\]]+? of '([^']+?)' ---", document_context or "")
        filename_hint = file_match.group(1).strip() if file_match else "the knowledge base"

        if context_block:
            if requested_page:
                # User asked about a specific page — give very explicit instructions
                user_content = (
                    f"The user is asking: \"{query.strip()}\"\n\n"
                    f"You are reading **Page {requested_page}** of **{filename_hint}**.\n\n"
                    f"The extracted content from Page {requested_page} is provided below.\n\n"
                    "---\n"
                    f"{context_block}\n"
                    "---\n\n"
                    f"## Your Task\n"
                    f"Answer the user's question **using ONLY the content from Page {requested_page}** above.\n\n"
                    "**Format your response as follows:**\n"
                    f"1. Start with: **📄 Page {requested_page} — {filename_hint}**\n"
                    "2. Use headings, bullet points, or tables to organise the information clearly.\n"
                    "3. Be concise — summarise and explain, don't just copy-paste raw text.\n"
                    f"4. End with: **📌 Source: Page {requested_page} of {filename_hint}**\n\n"
                    "If Page " + str(requested_page) + " has no relevant content for this question, say so clearly."
                )
            elif document_only:
                user_content = (
                    f"The user is asking: \"{query.strip()}\"\n\n"
                    f"The uploaded document content is provided below:\n\n"
                    "---\n"
                    f"{context_block}\n"
                    "---\n\n"
                    "**Format your response:**\n"
                    "- State which page(s) you are reading from at the top.\n"
                    "- Use headings and bullet points — not long paragraphs.\n"
                    "- If the document covers multiple pages, organise your answer by page.\n"
                    "- End with: **📌 Source: [filename, page numbers]**\n"
                    "- Do NOT assume the document is about aluminium unless it clearly is."
                )
            else:
                user_content = (
                    f"USER QUESTION: \"{query.strip()}\"\n\n"
                    f"CONTEXT PROVIDED:\n"
                    f"---\n"
                    f"{context_block}\n"
                    f"---\n\n"
                    f"INSTRUCTIONS:\n"
                    f"- Answer the question using ONLY the context above.\n"
                    f"- If you find multiple relevant details, use a Markdown Table.\n"
                    f"- **Bold** critical product names and specifications.\n"
                    f"- If the answer is not in the context, say: \"I don't have enough specific information in the current documents to answer that accurately.\""
                )
        else:
            user_content = f"The user is asking: \"{query.strip()}\""

        return [{"role": "user", "content": user_content}]


    def _create_response(
        self,
        query: str,
        context: str,
        document_context: str = "",
        knowledge_context: str = "",
    ) -> str:
        """
        Create a response based on query, retrieved products, and optional document/knowledge context.
        """
        document_only = bool((document_context or knowledge_context) and not context.strip())
        requested_page = self._detect_page_request(query)
        
        # Combine contexts for message building
        combined_doc_context = ""
        if document_context:
            combined_doc_context += document_context
        if knowledge_context:
            if combined_doc_context:
                combined_doc_context += "\n\n"
            combined_doc_context += knowledge_context

        messages = self._build_llm_messages(
            query, context, combined_doc_context, document_only=document_only,
            requested_page=requested_page,
        )
        use_ollama_for_docs = getattr(self.config, "USE_OLLAMA_FOR_DOCUMENTS", False)
        ollama_base = getattr(self.config, "OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = getattr(self.config, "OLLAMA_MODEL", "llama3.2")

        # When we have any document context (session OR global), prefer Ollama for specialist QA.
        doc_max_tokens = getattr(self.config, "DOC_LLM_MAX_TOKENS", 1024)
        if combined_doc_context and use_ollama_for_docs:
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

        # Fallback to local LLM or template if Ollama is off or failed
        if getattr(self.config, "LOCAL_LLM_ENABLED", False):
            try:
                from src.chatbot.local_llm import generate_answer
                default_tokens = getattr(self.config, "LOCAL_LLM_MAX_NEW_TOKENS", 256)
                max_tokens = doc_max_tokens if combined_doc_context else default_tokens
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

        # Final Fallback: echo context when LLM is unavailable.
        if combined_doc_context:
            if document_only:
                return (
                    "I've read your document. Here is the content I have:\n\n"
                    f"{combined_doc_context[:4000]}{'...' if len(combined_doc_context) > 4000 else ''}\n\n"
                    "Ask me to summarize or explain any part, or about budget/quotation if it applies."
                )
            intro = "I've read your document."
            if context.strip():
                intro = "I've read your document and matched relevant jobs/products."
            return f"""{intro}\n\nDocument:\n{combined_doc_context[:3000]}{'...' if len(combined_doc_context) > 3000 else ''}\n\nRelated products:\n{context}\n\nAsk follow-up questions (summarize, budget, quotation)."""

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
            knowledge_context = ""
            try:
                document_context = self._get_document_context_for_session(session_id, user_message) or ""
                knowledge_context = self._get_global_knowledge_context(user_message) or ""
            except Exception as doc_err:
                logger.exception("Context retrieval failed: %s", doc_err)

            has_doc = bool(document_context or knowledge_context)
            is_product_explicit = any(k in normalized for k in ["product", "aluminum", "aluminium", "alloy", "price", "cost", "specifications", "applications"])
            
            # Context-first: If we have documents, favor them
            is_doc_summary = self._is_document_summary_request(normalized) or (
                has_doc and self._wants_document_answer(normalized)
            ) or (has_doc and not is_product_explicit)

            # Retrieve products only when the question is not purely about documents
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
                    if has_doc:
                        # Answer only from the document/knowledge base
                        response_text = self._create_response(
                            user_message, "", document_context=document_context, knowledge_context=knowledge_context
                        )
                        products = []
                    else:
                        # No document context found
                        response_text = (
                            "I couldn't find relevant information in the uploaded documents or knowledge base. "
                            "Please ensure the information you're looking for is included in the PDFs."
                        )
                else:
                    if has_doc:
                        response_text = self._create_response(
                            user_message, context or "", document_context=document_context, knowledge_context=knowledge_context
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
    def chat_stream(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """
        Streaming version of chat. Yields chunks of text.
        """
        if not query.strip():
            yield "Please provide a message."
            return

        # 1. Retrieve Context
        products = self.retriever.retrieve(query)
        context = self._format_products_context(products)
        
        document_context = ""
        knowledge_context = ""
        try:
            document_context = self._get_document_context_for_session(session_id, query) or ""
            knowledge_context = self._get_global_knowledge_context(query) or ""
        except Exception as e:
            logger.error("Context retrieval failed: %s", e)

        combined_doc_context = ""
        if document_context: combined_doc_context += document_context
        if knowledge_context:
            if combined_doc_context: combined_doc_context += "\n\n"
            combined_doc_context += knowledge_context

        document_only = bool(combined_doc_context and not context.strip())
        requested_page = self._detect_page_request(query)

        # 2. Build Messages
        messages = self._build_llm_messages(
            query, context, combined_doc_context, document_only=document_only,
            requested_page=requested_page,
        )

        # 3. Stream from LLM
        use_ollama = getattr(self.config, "USE_OLLAMA_FOR_DOCUMENTS", False)
        ollama_base = getattr(self.config, "OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = getattr(self.config, "OLLAMA_MODEL", "llama3.2")

        full_response = ""
        if use_ollama:
            try:
                from src.chatbot.ollama_llm import stream_answer_with_ollama
                for chunk in stream_answer_with_ollama(
                    system_prompt=self.system_prompt,
                    messages=messages,
                    base_url=ollama_base,
                    model=ollama_model,
                ):
                    full_response += chunk
                    yield chunk
            except Exception as e:
                logger.warning("Streaming failed: %s", e)
                yield "Error during streaming. Please try again."
        else:
            # Fallback to non-streaming chat if Ollama is off
            resp_obj = self.chat(query, session_id, user_id)
            yield resp_obj.get("message", "Internal Error")
            return

        # 4. Save to history (after streaming finishes)
        if full_response:
            user_msg = self._build_message('user', query, session_id, user_id)
            ai_msg = self._build_message('assistant', full_response, session_id, user_id)
            self._save_message(user_msg)
            self._save_message(ai_msg)
