import os
from dataclasses import dataclass
from pathlib import Path


def load_env() -> None:
    path = Path(__file__).with_name(".env")
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    model: str
    base_url: str
    api_key: str
    temperature: float = 0.2
    timeout: float = 90.0

    @classmethod
    def load(cls):
        load_env()
        return cls(
            model=os.getenv("LLM_MODEL", "llama3.2"),
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/"),
            api_key=os.getenv("LLM_API_KEY", "ollama"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            timeout=float(os.getenv("LLM_TIMEOUT", "180")),
        )
