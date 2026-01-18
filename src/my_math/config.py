"""Configuration loader for MyMath game."""

import os
from pathlib import Path
from typing import Any

import yaml


def get_project_root() -> Path:
    """Get the project root directory."""
    # Try to find config.yaml starting from current directory and going up
    current = Path.cwd()

    # Check if we're in the project root
    if (current / "config.yaml").exists():
        return current

    # Check if we're in src/my_math
    if current.name == "my_math" and (current.parent.parent / "config.yaml").exists():
        return current.parent.parent

    # Check if we're in src
    if current.name == "src" and (current.parent / "config.yaml").exists():
        return current.parent

    # Try the directory of this file
    this_file = Path(__file__).resolve()
    project_root = this_file.parent.parent.parent
    if (project_root / "config.yaml").exists():
        return project_root

    # Default to current directory
    return current


class Config:
    """Configuration class for the MyMath game."""

    def __init__(self, config_path: str | Path | None = None):
        """Load configuration from YAML file.

        Args:
            config_path: Path to the configuration file. If None, will look for
                        config.yaml in the project root.
        """
        self.project_root = get_project_root()

        if config_path is None:
            config_path = self.project_root / "config.yaml"

        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key (supports nested keys with dot notation).

        Args:
            key: Configuration key (e.g., 'sound.enabled' or 'title')
            default: Default value if key not found

        Returns:
            The configuration value or default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_path(self, key: str, default: str = "") -> Path:
        """Get a path configuration value, resolved relative to project root.

        Args:
            key: Configuration key for the path
            default: Default path if key not found

        Returns:
            Resolved Path object
        """
        path_str = self.get(key, default)
        if not path_str:
            return Path(default)
        return self.project_root / path_str

    @property
    def title(self) -> str:
        """Get the game title."""
        return self.get("title", "MyMath")

    @property
    def images_folder(self) -> Path:
        """Get the images folder path."""
        return self.get_path("images_folder", "data/images")

    @property
    def sound_enabled(self) -> bool:
        """Check if sound is enabled."""
        return self.get("sound.enabled", True)

    @property
    def correct_sound_folder(self) -> Path:
        """Get the correct answer sounds folder path."""
        return self.get_path("sound.correct_sound", "data/reactions")

    @property
    def wrong_sound(self) -> Path:
        """Get the wrong answer sound path."""
        return self.get_path("sound.wrong_sound", "data/reactions/woops.wav")

    @property
    def window_width(self) -> int:
        """Get the window width."""
        return self.get("window.width", 1024)

    @property
    def window_height(self) -> int:
        """Get the window height."""
        return self.get("window.height", 768)

    @property
    def fullscreen(self) -> bool:
        """Check if fullscreen mode is enabled."""
        return self.get("window.fullscreen", False)

    # Counting game settings
    @property
    def counting_max_count(self) -> int:
        """Get the maximum count for counting game."""
        return self.get("counting.max_count", 5)

    @property
    def counting_min_count(self) -> int:
        """Get the minimum count for counting game."""
        return self.get("counting.min_count", 1)

    @property
    def counting_rounds(self) -> int:
        """Get the number of rounds for counting game."""
        return self.get("counting.rounds", 5)

    @property
    def counting_image_size(self) -> int:
        """Get the image size for counting game."""
        return self.get("counting.image_size", 80)

    @property
    def counting_numbers_delay(self) -> int:
        """Get the delay before showing number buttons in milliseconds."""
        return self.get("counting.numbers_delay_ms", 1500)

    @property
    def counting_next_round_delay(self) -> int:
        """Get the delay before next round in milliseconds."""
        return self.get("counting.next_round_delay_ms", 2000)

    @property
    def counting_highlight_duration(self) -> int:
        """Get the highlight duration in milliseconds."""
        return self.get("counting.highlight_duration_ms", 1500)


# Global config instance
_config: Config | None = None


def load_config(config_path: str | Path | None = None) -> Config:
    """Load or get the global configuration.

    Args:
        config_path: Path to configuration file (only used on first call)

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def get_config() -> Config:
    """Get the global configuration (must be loaded first).

    Returns:
        Config instance

    Raises:
        RuntimeError: If config hasn't been loaded yet
    """
    if _config is None:
        return load_config()
    return _config
