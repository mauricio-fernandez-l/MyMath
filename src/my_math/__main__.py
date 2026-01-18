"""Entry point for the MyMath game."""

from .config import load_config
from .game import run_game


def main():
    """Main entry point for the application."""
    config = load_config()
    run_game(config)


if __name__ == "__main__":
    main()
