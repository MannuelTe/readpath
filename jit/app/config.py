import os
from dataclasses import dataclass


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("JIT_DB_PATH", "data/jit.db")
    latency_target_ms: float = _float("JIT_LATENCY_TARGET_MS", 140)
    latency_jitter_ms: float = _float("JIT_LATENCY_JITTER_MS", 50)
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    request_timeout_seconds: float = _float("JIT_REQUEST_TIMEOUT_SECONDS", 60)


settings = Settings()

