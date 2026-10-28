import logging
import os
import sys

def setup_logging() -> None:
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=level, stream=sys.stdout, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # uvicorn über das Root-Format laufen lassen, eigene Access-Logs aus
    # (die Middleware loggt stattdessen eine Zeile pro Request)
    for name in ("uvicorn", "uvicorn.error"):
        log = logging.getLogger(name)
        log.handlers.clear()
        log.propagate = True
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Bibliotheken, die auf DEBUG Header/Keys ausgeben könnten
    for name in ("anthropic", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)