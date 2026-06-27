import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


_USE_COLOR = (hasattr(sys.stdout, "isatty") and sys.stdout.isatty()) or os.environ.get("PYEX_FORCE_COLOR") == "1"


class _Color:
    RESET    = "\033[0m"  if _USE_COLOR else ""
    BOLD     = "\033[1m"  if _USE_COLOR else ""
    DIM      = "\033[2m"  if _USE_COLOR else ""
    DEBUG    = "\033[36m" if _USE_COLOR else ""
    INFO     = "\033[32m" if _USE_COLOR else ""
    WARNING  = "\033[33m" if _USE_COLOR else ""
    ERROR    = "\033[31m" if _USE_COLOR else ""
    CRITICAL = "\033[35m" if _USE_COLOR else ""
    PRIMARY  = "\033[94m" if _USE_COLOR else ""
    SECONDARY= "\033[96m" if _USE_COLOR else ""
    TIME     = "\033[90m" if _USE_COLOR else ""


_LEVEL_STYLES: dict[int, tuple[str, str]] = {
    logging.DEBUG:    (_Color.DEBUG,    "DBG"),
    logging.INFO:     (_Color.INFO,     "INF"),
    logging.WARNING:  (_Color.WARNING,  "WRN"),
    logging.ERROR:    (_Color.ERROR,    "ERR"),
    logging.CRITICAL: (_Color.CRITICAL, "CRT"),
}


class _ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color, label = _LEVEL_STYLES.get(record.levelno, (_Color.RESET, "???"))
        tag_color = _Color.PRIMARY if record.name.startswith("PyEx") else _Color.SECONDARY
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        line = (
            f"{_Color.TIME}{ts}{_Color.RESET} "
            f"{color}{_Color.BOLD}[{label}]{_Color.RESET} "
            f"{tag_color}[{record.name}]{_Color.RESET} "
            f"{record.getMessage()}"
        )
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


class _FileFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        _, label = _LEVEL_STYLES.get(record.levelno, (_Color.RESET, "???"))
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"{ts} [{label}] [{record.name}] {record.getMessage()}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


class Logger:
    def __init__(self, name: str, _logger: logging.Logger):
        self.name = name
        self._log = _logger

    def debug(self, msg, *a, **kw):     self._log.debug(str(msg), *a, **kw)
    def info(self, msg, *a, **kw):      self._log.info(str(msg), *a, **kw)
    def warn(self, msg, *a, **kw):      self._log.warning(str(msg), *a, **kw)
    def warning(self, msg, *a, **kw):   self._log.warning(str(msg), *a, **kw)
    def error(self, msg, *a, **kw):     self._log.error(str(msg), *a, **kw)
    def critical(self, msg, *a, **kw):  self._log.critical(str(msg), *a, **kw)
    def exception(self, msg, *a, **kw): self._log.exception(str(msg), *a, **kw)

    def success(self, msg, *a, **kw):
        self._log.info(f"✓ {msg}", *a, **kw)

    def section(self, title: str):
        sep = "─" * 50
        self._log.info(f"\n{sep}\n  {title}\n{sep}")

    def __repr__(self):
        return f"<Logger '{self.name}'>"


def _safe_stdout():
    try:
        if sys.stdout is not None:
            sys.stdout.write("")
            return sys.stdout
    except Exception:
        pass
    return open(os.devnull, "w")


class _LogManager:
    def __init__(self):
        self._initialized = False
        self._log_file: Optional[Path] = None
        self._level = logging.DEBUG
        self._loggers: dict[str, Logger] = {}
        self._root = logging.getLogger("PyEx")
        self._root.setLevel(logging.DEBUG)
        self._root.propagate = False
        self._console_handler: Optional[logging.StreamHandler] = None
        self._file_handler: Optional[logging.FileHandler] = None
        self._setup_console()

    def _setup_console(self):
        try:
            self._console_handler = logging.StreamHandler(_safe_stdout())
            self._console_handler.setFormatter(_ConsoleFormatter())
            self._console_handler.setLevel(logging.DEBUG)
            self._root.addHandler(self._console_handler)
        except Exception:
            pass

    def init(
        self,
        namespace: str = "PyEx",
        log_dir: Optional[Path] = None,
        level: int = logging.DEBUG,
        log_to_file: bool = True,
        log_to_console: bool = True,
    ):
        if self._initialized:
            return

        self._namespace = namespace
        self._level = level

        if self._console_handler:
            self._console_handler.setLevel(level if log_to_console else logging.CRITICAL + 1)
        self._root.setLevel(level)

        if log_to_file:
            if log_dir is None:
                log_dir = Path("logs")
            log_dir = Path(log_dir)
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self._log_file = log_dir / f"{namespace.lower()}_{timestamp}.log"
                self._file_handler = logging.FileHandler(self._log_file, encoding="utf-8")
                self._file_handler.setFormatter(_FileFormatter())
                self._file_handler.setLevel(logging.DEBUG)
                self._root.addHandler(self._file_handler)
            except Exception as e:
                self._root.warning(f"Could not create log file: {e}")

        self._initialized = True

        boot = self.get(f"{namespace}.Logger")
        boot.section(f"{namespace} — Logger initialized")
        if self._log_file:
            boot.info(f"Log file: {self._log_file.resolve()}")

    def get(self, name: str) -> Logger:
        if name not in self._loggers:
            full_name = name if name.startswith(self._namespace) else f"{self._namespace}.{name}"
            inner = logging.getLogger(full_name)
            inner.setLevel(self._level)
            inner.propagate = True
            self._loggers[name] = Logger(full_name, inner)
        return self._loggers[name]

    def set_level(self, level: int):
        self._level = level
        self._root.setLevel(level)
        if self._console_handler:
            self._console_handler.setLevel(level)
        for logger in self._loggers.values():
            logger._log.setLevel(level)

    def disable_console(self):
        if self._console_handler:
            self._console_handler.setLevel(logging.CRITICAL + 1)

    def enable_console(self):
        if self._console_handler:
            self._console_handler.setLevel(self._level)

    def close(self):
        if self._file_handler:
            self._file_handler.close()
            self._root.removeHandler(self._file_handler)

    @property
    def log_file(self) -> Optional[Path]:
        return self._log_file

    @property
    def initialized(self) -> bool:
        return self._initialized


_manager = _LogManager()


def init(
    namespace: str = "PyEx",
    log_dir: Optional[Path] = None,
    level: int = logging.DEBUG,
    log_to_file: bool = True,
    log_to_console: bool = True,
):
    _manager.init(
        namespace=namespace,
        log_dir=log_dir,
        level=level,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
    )


def get_logger(name: str) -> Logger:
    return _manager.get(name)


def set_level(level: int):
    _manager.set_level(level)


def disable_console():
    _manager.disable_console()


def enable_console():
    _manager.enable_console()


def get_log_file() -> Optional[Path]:
    return _manager.log_file


def close():
    _manager.close()