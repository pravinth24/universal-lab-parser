"""Configuration management for Universal Lab Parser."""

from pathlib import Path
from typing import Optional, Dict, Any
import json
from pydantic import BaseModel, Field


class ParserConfig(BaseModel):
    """Configuration for a specific parser."""

    enabled: bool = True
    timeout_seconds: int = 300
    max_file_size_mb: int = 500
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class PerformanceConfig(BaseModel):
    """Performance-related configuration."""

    max_workers: int = 4
    chunk_size: int = 10000
    enable_caching: bool = True
    cache_dir: Path = Path.home() / ".cache" / "universal_lab_parser"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    log_to_file: bool = False
    log_file: Optional[Path] = None
    log_to_console: bool = True


class UniversalLabParserConfig(BaseModel):
    """Main configuration for Universal Lab Parser."""

    parsers: Dict[str, ParserConfig] = Field(default_factory=lambda: {
        "waters": ParserConfig(),
        "agilent": ParserConfig(),
        "thermo": ParserConfig(),
    })
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    auto_detect: bool = True
    strict_mode: bool = False  # If True, raise errors on warnings

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_file(cls, filepath: Path) -> "UniversalLabParserConfig":
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_file(self, filepath: Path) -> None:
        """Save configuration to JSON file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.model_dump(), f, indent=2, default=str)

    @classmethod
    def load_default(cls) -> "UniversalLabParserConfig":
        """Load default configuration, with optional user overrides."""
        config_path = Path.home() / ".config" / "universal_lab_parser" / "config.json"

        if config_path.exists():
            return cls.from_file(config_path)
        else:
            return cls()


# Global configuration instance
_config: Optional[UniversalLabParserConfig] = None


def get_config() -> UniversalLabParserConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = UniversalLabParserConfig.load_default()
    return _config


def set_config(config: UniversalLabParserConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = UniversalLabParserConfig()
