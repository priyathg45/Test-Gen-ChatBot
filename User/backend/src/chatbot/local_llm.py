"""Local LLM wrapper for aluminium chatbot.

This loads a causal language model from Hugging Face using `transformers`
and exposes a simple `generate_answer` function. It is fully local:
no external API calls are made.
"""
from __future__ import annotations

import logging
from typing import List, Dict

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

_MODEL = None
_TOKENIZER = None


def _load_model(model_name: str, device: str = "auto"):
    """Lazy-load the local LLM."""
    global _MODEL, _TOKENIZER
    if _MODEL is not None and _TOKENIZER is not None:
        return _MODEL, _TOKENIZER

    logger.info("Loading local LLM model: %s", model_name)

    if device == "cuda" and torch.cuda.is_available():
        torch_device = "cuda"
    elif device in ("cpu", "cuda"):
        torch_device = device
    else:
        torch_device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    # Ensure a pad token exists for left-padded generation.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.to(torch_device)
    model.eval()

    _MODEL = model
    _TOKENIZER = tokenizer
    logger.info("Local LLM loaded on device: %s", torch_device)
    return model, tokenizer


def build_prompt(system_prompt: str, messages: List[Dict[str, str]]) -> str:
    """Flatten simple chat messages into a single prompt string.

    This is a generic format that works for most instruction-tuned models.
    If you adopt a specific chat template (e.g. Llama, Qwen), you can
    adjust this to match that template.
    """
    parts = []
    if system_prompt:
        parts.append(f"System: {system_prompt.strip()}\n")

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "").strip()
        if not content:
            continue
        if role == "user":
            parts.append(f"User: {content}\n")
        elif role == "assistant":
            parts.append(f"Assistant: {content}\n")
        else:
            parts.append(f"{role.capitalize()}: {content}\n")

    parts.append("Assistant:")
    return "\n".join(parts)


def generate_answer(
    system_prompt: str,
    messages: List[Dict[str, str]],
    model_name: str,
    device: str = "auto",
    max_new_tokens: int = 256,
    temperature: float = 0.2,
) -> str:
    """Generate an answer using the local LLM.

    Args:
        system_prompt: High-level instructions for the assistant.
        messages: List of {'role': 'user'|'assistant', 'content': str}.
        model_name: Hugging Face model id to load locally.
        device: 'cpu' | 'cuda' | 'auto'.
        max_new_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
    """
    model, tokenizer = _load_model(model_name, device=device)

    prompt = build_prompt(system_prompt, messages)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=temperature,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    # Heuristic: return only text after the last "Assistant:" marker.
    marker = "Assistant:"
    if marker in generated:
        return generated.split(marker)[-1].strip()
    return generated.strip()

