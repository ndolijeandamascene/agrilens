"""
AgriLens Local Neural Model Runtime Service.
Provides 100% in-process local neural LLM inference via llama-cpp-python.
Operates with zero external network dependencies (no Ollama, no cloud API keys).
"""
import os
import time
import logging
import threading
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

_model_instance: Any = None
_model_lock = threading.Lock()
_load_error: Optional[str] = None

_download_lock = threading.Lock()
_download_thread: Optional[threading.Thread] = None
_download_progress: Dict[str, Any] = {
    'is_downloading': False,
    'total_bytes': 0,
    'downloaded_bytes': 0,
    'speed_mb_s': 0.0,
    'progress_pct': 0.0,
    'error': None,
}

HF_DOWNLOAD_URL = "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
MIN_FILE_BYTES = 1_900_000_000


def find_any_existing_model() -> Optional[str]:
    """
    Checks all candidate paths and environment configurations to verify
    if the neural model weights already exist on disk (size >= 1.9 GB).
    """
    configured = getattr(settings, 'QWEN_MODEL_PATH', '')
    candidates = [
        configured,
        str(settings.BASE_DIR / 'data' / 'models' / 'qwen2.5-3b-instruct-q4_k_m.gguf'),
        '/app/data/models/qwen2.5-3b-instruct-q4_k_m.gguf',
        '/app/models/qwen2.5-3b-instruct-q4_k_m.gguf',
        r'C:\Users\ndoli\Documents\WEBAPP\IHKIP\models\qwen2.5-3b-instruct-q4_k_m.gguf',
        r'C:\Users\ndoli\Documents\WEBAPP\agrilens\data\models\qwen2.5-3b-instruct-q4_k_m.gguf',
        str(Path.home() / '.cache' / 'agrilens' / 'models' / 'qwen2.5-3b-instruct-q4_k_m.gguf'),
    ]
    for c in candidates:
        if c and os.path.isfile(c) and os.path.getsize(c) >= MIN_FILE_BYTES:
            return c
    return None


def _get_configured_model_path() -> str:
    """Retrieves and validates the GGUF model path from settings or default locations."""
    existing = find_any_existing_model()
    if existing:
        return existing

    configured = getattr(settings, 'QWEN_MODEL_PATH', '')
    return configured or ('/app/data/models/qwen2.5-3b-instruct-q4_k_m.gguf' if os.name != 'nt' else str(settings.BASE_DIR / 'data' / 'models' / 'qwen2.5-3b-instruct-q4_k_m.gguf'))


def _run_background_download(dest_file_path: str):
    global _download_progress

    # Pre-check: Ensure model was not downloaded or copied concurrently
    existing = find_any_existing_model()
    if existing:
        logger.info("[OK] Model already present at %s. Cancelling download.", existing)
        with _download_lock:
            _download_progress['is_downloading'] = False
            _download_progress['progress_pct'] = 100.0
        QwenModelRuntime.reload_model()
        return

    part_path = dest_file_path + ".part"
    os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)

    with _download_lock:
        _download_progress['is_downloading'] = True
        _download_progress['error'] = None
        _download_progress['progress_pct'] = 0.0

    logger.info("Starting background download of AgriLens AI weights to: %s", dest_file_path)
    start_time = time.time()
    try:
        req = urllib.request.Request(
            HF_DOWNLOAD_URL,
            headers={"User-Agent": "AgriLens-Neural-Runtime/1.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp, open(part_path, "wb") as f_out:
            total_size = resp.headers.get("Content-Length")
            total_bytes = int(total_size) if total_size else 0
            _download_progress['total_bytes'] = total_bytes
            downloaded = 0
            block_size = 1024 * 1024  # 1 MB

            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f_out.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                elapsed = max(1.0, now - start_time)
                _download_progress['downloaded_bytes'] = downloaded
                _download_progress['progress_pct'] = round((downloaded / total_bytes * 100), 1) if total_bytes else 0.0
                _download_progress['speed_mb_s'] = round((downloaded / (1024 * 1024)) / elapsed, 2)

        if os.path.exists(dest_file_path):
            os.remove(dest_file_path)
        os.rename(part_path, dest_file_path)
        logger.info("AgriLens AI weights successfully downloaded to: %s in %.1fs", dest_file_path, time.time() - start_time)
        with _download_lock:
            _download_progress['is_downloading'] = False
            _download_progress['progress_pct'] = 100.0

        QwenModelRuntime.reload_model()
    except Exception as exc:
        logger.error("Failed to download neural model weights in background: %s", exc)
        with _download_lock:
            _download_progress['is_downloading'] = False
            _download_progress['error'] = str(exc)
        if os.path.exists(part_path):
            try:
                os.remove(part_path)
            except OSError:
                pass


def trigger_model_download_if_needed(target_path: Optional[str] = None) -> bool:
    """Verifies whether model exists on disk before initiating background download."""
    global _download_thread

    # Check all candidate paths first
    existing = find_any_existing_model()
    if existing:
        logger.info("[SKIP DOWNLOAD] Neural weights already exist on disk at: %s (%.1f MB).", existing, os.path.getsize(existing) / (1024 * 1024))
        return False

    dest_path = target_path or _get_configured_model_path()
    if os.path.isfile(dest_path) and os.path.getsize(dest_path) >= MIN_FILE_BYTES:
        logger.info("[SKIP DOWNLOAD] Target path already has verified model file: %s", dest_path)
        return False

    with _download_lock:
        if _download_progress['is_downloading']:
            return True
        _download_thread = threading.Thread(
            target=_run_background_download,
            args=(dest_path,),
            daemon=True,
            name="AgriLensModelDownloader"
        )
        _download_thread.start()
        return True


def _load_qwen_model() -> Any:
    """Loads the GGUF model once as a singleton using memory mapping."""
    global _load_error

    enabled = getattr(settings, 'QWEN_LLM_ENABLED', True)
    if not enabled:
        _load_error = "AgriLens AI LLM is disabled via settings (QWEN_LLM_ENABLED=False)."
        logger.info(_load_error)
        return None

    model_path = find_any_existing_model()
    if not model_path:
        _load_error = "AgriLens AI GGUF model file not found in any candidate directory."
        logger.warning(_load_error)
        # Check and initiate download only if missing everywhere
        if getattr(settings, 'DOWNLOAD_QWEN_MODEL', True):
            trigger_model_download_if_needed()
        return None

    try:
        from llama_cpp import Llama
    except Exception as exc:
        _load_error = f"Failed to load llama-cpp-python: {exc}"
        logger.error(_load_error)
        return None

    n_ctx = int(getattr(settings, 'QWEN_MODEL_N_CTX', 2048))
    configured_threads = getattr(settings, 'QWEN_MODEL_N_THREADS', 0)
    if configured_threads and int(configured_threads) > 0:
        n_threads = int(configured_threads)
    else:
        n_threads = max(2, min(8, os.cpu_count() or 4))
    n_batch = int(getattr(settings, 'QWEN_MODEL_N_BATCH', 512))

    logger.info("Initializing in-process AgriLens AI from: %s (n_ctx=%d, threads=%d)", model_path, n_ctx, n_threads)

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
        _load_error = None
        logger.info("AgriLens AI neural model loaded successfully into process memory.")
        return model
    except Exception as exc:
        _load_error = f"Failed to instantiate Llama model: {exc}"
        logger.error(_load_error, exc_info=True)
        return None


class QwenModelRuntime:
    """Thread-safe gateway to the local AgriLens AI neural LLM."""

    @classmethod
    def _get_model(cls) -> Any:
        global _model_instance
        if _model_instance is not None:
            return _model_instance

        with _model_lock:
            if _model_instance is None:
                _model_instance = _load_qwen_model()
        return _model_instance

    @classmethod
    def is_available(cls) -> bool:
        """Returns True if the neural model is loaded and ready for inference."""
        return cls._get_model() is not None

    @classmethod
    def reload_model(cls) -> bool:
        """Forces a reload attempt of the model from disk into RAM."""
        global _model_instance
        with _model_lock:
            _model_instance = _load_qwen_model()
        return _model_instance is not None

    @classmethod
    def get_load_error(cls) -> Optional[str]:
        cls._get_model()
        return _load_error

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Provides operational telemetry on model file, loading state, and downloads."""
        target_path = _get_configured_model_path()
        file_exists = os.path.isfile(target_path) if target_path else False
        file_size_mb = round(os.path.getsize(target_path) / (1024 * 1024), 1) if file_exists else 0.0

        return {
            'ai_engine': 'AgriLens AI (Local In-Process Neural Runtime)',
            'model_loaded': cls.is_available(),
            'model_path': target_path,
            'file_exists': file_exists,
            'file_size_mb': file_size_mb,
            'download': dict(_download_progress),
            'load_error': _load_error,
        }

    @classmethod
    def generate(
        cls,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Executes one ChatML inference pass over AgriLens AI.
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
                stop=stop or ["<|im_end|>", "<|endoftext|>", "<|im_start|>", "\n\nUser Question:", "\n\nUser Inquiry:"],
            )
            choices = output.get('choices', [])
            if choices and 'message' in choices[0] and 'content' in choices[0]['message']:
                content = choices[0]['message']['content']
                return content.strip() if content else None
            return None
        except Exception as exc:
            logger.warning("AgriLens AI inference error: %s", exc)
            return None
