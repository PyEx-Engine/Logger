# Logger

**Colored console + file logger — extracted from [PyEx Engine](https://github.com/PyEx-Engine/PyEx).**

---

## Features

- Colored ANSI output in console (auto-disabled if no TTY)
- File logging with timestamp in filename
- Log levels : `DBG` `INF` `WRN` `ERR` `CRT`
- `success()` and `section()` helpers
- Safe stdout — works inside PyInstaller `.exe`
- Configurable namespace, log directory, level
- Enable / disable console at runtime

---

## Usage

```python
from logger import init, get_logger

init(namespace="MyApp", log_dir="logs", log_to_file=True)

log = get_logger("MyModule")

log.debug("details")
log.info("started")
log.success("all good")
log.warn("something's off")
log.error("something broke")
log.critical("fatal")
log.section("New section")
```

**Console output :**
```
12:34:56.789 [INF] [MyApp.MyModule] ✓ all good
12:34:56.790 [WRN] [MyApp.MyModule] something's off
```

**File output** (`logs/myapp_2026-06-24_12-34-56.log`) :
```
2026-06-24 12:34:56.789 [INF] [MyApp.MyModule] ✓ all good
2026-06-24 12:34:56.790 [WRN] [MyApp.MyModule] something's off
```

---

## API

```python
init(namespace, log_dir, level, log_to_file, log_to_console)
get_logger(name)   → Logger
set_level(level)
disable_console()
enable_console()
get_log_file()     → Path | None
close()
```

```python
log.debug(msg)
log.info(msg)
log.warn(msg)
log.error(msg)
log.critical(msg)
log.exception(msg)
log.success(msg)    # info with ✓ prefix
log.section(title)  # prints a separator
```

---

## Environment

| Variable | Effect |
|---|---|
| `PYEX_FORCE_COLOR=1` | Force colors even if not a TTY |

---

*Part of the [PyEx Engine](https://github.com/PyEx-Engine/PyEx) project.*
