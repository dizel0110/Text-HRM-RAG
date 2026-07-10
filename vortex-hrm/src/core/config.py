"""
VORTEX configuration system.
Zero dependencies — pure dataclasses with dict loader.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    mode: str = "mock"                     # "mock" | "ollama" | "openai"
    model: str = "mock"                    # model name
    base_url: Optional[str] = None         # e.g. http://localhost:11434/v1
    temperature: float = 0.0
    max_tokens: int = 2048
    api_key: Optional[str] = None          # only for openai mode
    timeout: int = 300                     # request timeout in seconds (CPU models are slow)


@dataclass
class EngineConfig:
    max_spirals: int = 15
    confidence_threshold: float = 0.85
    entropy_stall_limit: int = 3
    context_budget: int = 8192
    verbose: bool = False


@dataclass
class VORTEXConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    engine: EngineConfig = field(default_factory=EngineConfig)

    @classmethod
    def from_dict(cls, d: dict) -> "VORTEXConfig":
        llm_raw = d.get("llm", {})
        engine_raw = d.get("engine", {})
        return cls(
            llm=LLMConfig(
                mode=llm_raw.get("mode", "mock"),
                model=llm_raw.get("model", "mock"),
                base_url=llm_raw.get("base_url"),
                temperature=llm_raw.get("temperature", 0.0),
                max_tokens=llm_raw.get("max_tokens", 2048),
                api_key=llm_raw.get("api_key"),
                timeout=llm_raw.get("timeout", 300),
            ),
            engine=EngineConfig(
                max_spirals=engine_raw.get("max_spirals", 15),
                confidence_threshold=engine_raw.get("confidence_threshold", 0.85),
                entropy_stall_limit=engine_raw.get("entropy_stall_limit", 3),
                context_budget=engine_raw.get("context_budget", 8192),
                verbose=engine_raw.get("verbose", False),
            ),
        )

    @classmethod
    def from_yaml(cls, path: str) -> "VORTEXConfig":
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required to load .yaml configs. Run: pip install pyyaml")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
