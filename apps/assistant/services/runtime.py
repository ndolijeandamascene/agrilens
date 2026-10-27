"""
AgriLens Qwen 2.5 3B Model Runtime Service.
Provides 100% in-process local neural LLM inference via llama-cpp-python.
Operates with zero external network dependencies (no Ollama, no cloud API keys).
"""
import os
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

_model_instance: Any = None
_model_lock = threading.Lock()
_load_attempted: bool = False
_load_error: Optional[str] = None


def _get_configured_model_path() -> str:
    """Retrieves and validates the GGUF model path from settings or default location."""
    configured = getattr(settings, 'QWEN_MODEL_PATH', '')
    if configured and os.path.isfile(configured):
        return configured

    # Candidate paths ordered by priority (Linux Docker container paths + local dev paths)
    candidates = [
        str(settings.BASE_DIR / 'data' / 'models' / 'qwen2.5-3b-instruct-q4_k_m.gguf'),
        '/app/data/models/qwen2.5-3b-instruct-q4_k_m.gguf',
        '/app/models/qwen2.5-3b-instruct-q4_k_m.gguf',
        r'C:\Users\ndoli\Documents\WEBAPP\IHKIP\models\qwen2.5-3b-instruct-q4_k_m.gguf',
        r'C:\Users\ndoli\Documents\WEBAPP\agrilens\data\models\qwen2.5-3b-instruct-q4_k_m.gguf',
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return configured or candidates[0]



def _load_qwen_model() -> Any:
    """Loads the GGUF model once as a singleton using memory mapping."""
    global _load_error

    enabled = getattr(settings, 'QWEN_LLM_ENABLED', True)
    if not enabled:
        _load_error = "Qwen LLM is disabled via settings (QWEN_LLM_ENABLED=False)."
        logger.info(_load_error)
        return None

    model_path = _get_configured_model_path()
    if not model_path or not os.path.isfile(model_path):
        _load_error = f"Qwen GGUF model file not found at: {model_path}"
        logger.warning(_load_error)
        return None

    try:
        from llama_cpp import Llama
    except ImportError:
        _load_error = "llama-cpp-python is not installed in the active environment."
        logger.error(_load_error)
        return None

    n_ctx = int(getattr(settings, 'QWEN_MODEL_N_CTX', 4096))
    n_threads = int(getattr(settings, 'QWEN_MODEL_N_THREADS', min(8, max(2, (os.cpu_count() or 4) - 1))))
    n_batch = int(getattr(settings, 'QWEN_MODEL_N_BATCH', 512))

    logger.info("Initializing in-process Qwen 2.5 3B from: %s (n_ctx=%d, threads=%d)", model_path, n_ctx, n_threads)

    try:
        model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_batch=n_batch,
            use_mmap=True,
            use_mlock=False,
            verbose=False,
            chat_format="chatml",
        )
        logger.info("Qwen 2.5 3B model loaded successfully into process memory.")
        return model
    except Exception as exc:
        _load_error = f"Failed to instantiate Llama model: {exc}"
        logger.error(_load_error, exc_info=True)
        return None


class QwenModelRuntime:
    """Thread-safe gateway to the local Qwen 2.5 3B neural LLM."""

    @classmethod
    def _get_model(cls) -> Any:
        global _model_instance, _load_attempted
        if _load_attempted:
            return _model_instance

        with _model_lock:
            if not _load_attempted:
                _model_instance = _load_qwen_model()
                _load_attempted = True
        return _model_instance

    @classmethod
    def is_available(cls) -> bool:
        """Returns True if Qwen 2.5 3B is loaded and ready for inference."""
        return cls._get_model() is not None

    @classmethod
    def get_load_error(cls) -> Optional[str]:
        cls._get_model()
        return _load_error

    @classmethod
    def generate(
        cls,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Executes one ChatML inference pass over Qwen 2.5 3B.
        Returns the generated text string, or None if unavailable.
        """
        model = cls._get_model()
        if model is None:
            return None

        _max_tokens = max_tokens if max_tokens is not None else int(getattr(settings, 'QWEN_MODEL_MAX_TOKENS', 450))
        _temperature = temperature if temperature is not None else float(getattr(settings, 'QWEN_MODEL_TEMPERATURE', 0.3))

        try:
            output = model.create_chat_completion(
                messages=messages,
                max_tokens=_max_tokens,
                temperature=_temperature,
                stop=stop or ["<|im_end|>", "<|endoftext|>"],
            )
            choices = output.get('choices', [])
            if choices and 'message' in choices[0] and 'content' in choices[0]['message']:
                content = choices[0]['message']['content']
                return content.strip() if content else None
            return None
        except Exception as exc:
            logger.warning("Qwen inference error: %s", exc)
            return None
