"""Side-effect-free structured logger lookup shared by Wright packages."""

import structlog


def get_logger(name: str):
    return structlog.get_logger(name)
