import sys
from pathlib import Path
from typing import Any

from loguru import logger


def setup_logger(
    log_dir: str = "logs",
    rotation: str = "10 MB",
    retention: str = "10 days",
    level: str = "INFO",
) -> Any:
    """
    Configures the loguru logger with rotation, retention, and console output.

    Args:
        log_dir (str): Directory where log files will be stored.
        rotation (str): file size or time to rotate logs (e.g., "10 MB", "1 day").
        retention (str): how long to keep logs (e.g., "10 days").
        level (str): Minimum logging level for the console.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Remove default handler to avoid duplicate logs
    logger.remove()

    # Add console handler (stderr)
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=level,
    )

    # Add standard file handler (human readable)
    logger.add(
        log_path / "autoreel.log",
        rotation=rotation,
        retention=retention,
        level="DEBUG",
        compression="zip",
    )

    # Add structured JSON handler for potential ELK stack or analysis
    logger.add(
        log_path / "autoreel.json.log",
        rotation=rotation,
        retention=retention,
        level="INFO",
        serialize=True,
    )

    # Add error specific file handler
    logger.add(log_path / "error.log", rotation=rotation, retention=retention, level="ERROR")

    logger.info(f"Logger initialized. Logs writing to {log_path.absolute()}")
    return logger
