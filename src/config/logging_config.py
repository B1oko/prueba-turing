import logging
import os


COLORS = {
    "DEBUG": "\033[36m",  # cyan
    "INFO": "\033[32m",  # green
    "WARNING": "\033[33m",  # yellow
    "ERROR": "\033[31m",  # red
    "CRITICAL": "\033[35m",  # magenta
}
RESET = "\033[0m"
GREY = "\033[90m"
BOLD = "\033[1m"


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = COLORS.get(record.levelname, RESET)
        record.levelname = f"{color}{BOLD}{record.levelname}{RESET}"
        record.name = f"{GREY}{record.name}{RESET}"
        record.asctime = self.formatTime(record, self.datefmt)
        record.asctime = f"{GREY}{record.asctime}{RESET}"
        return super().format(record)


def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    handler = logging.StreamHandler()
    handler.setFormatter(
        ColoredFormatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logging.basicConfig(level=log_level, handlers=[handler])

    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("uvicorn").addHandler(handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
