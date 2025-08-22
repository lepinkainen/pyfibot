# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack Guidelines

**IMPORTANT**: For general technology choices and project guidelines, refer to `/llm-shared/project_tech_stack.md` which contains the authoritative guidelines that may change over time.

### Python-Specific Guidelines

- Use "uv" for dependency management (already implemented in this project)
- Use "ruff" for linting and formatting (this project uses flake8 for linting)
- Use "mypy" for type checking as much as possible (already implemented for core files)
- When analyzing large codebases, use the `pyfuncs` tool: `python llm-shared/utils/pyfuncs.py --dir /path/to/project`

### Large Codebase Analysis

When analyzing large codebases that might exceed context limits, use the Gemini CLI with the `-p` flag:

- Analyzing entire codebases or large directories
- Comparing multiple large files
- Understanding project-wide patterns or architecture
- Checking for coding patterns or practices

Examples:
```bash
gemini -p "@pyfibot/ Summarise the architecture of this codebase"
gemini -p "@pyfibot/modules/ Explain the module system implementation"
gemini -p "@pyfibot/ Is the project test coverage on par with industry standards?"
```

## Development Commands

In general don't try to run `python3` directly, use the `uv run` command instead. This ensures that the correct Python environment is used and dependencies are managed properly.

### Available Tasks

- `task test` - Run specific test files with coverage (not all tests)
- `task test-ci` - Run tests in CI environment with XML coverage
- `task lint` - Run flake8 linting on pyfibot/ directory
- `task typecheck` - Run mypy type checking on core files only (botcore.py, pyfibot.py)
- `task format` - Format code with black
- `task format-check` - Check if code is formatted correctly
- `task build` - Build the project (runs tests, lint, and typecheck)
- `task dev-install` - Install with development dependencies
- `task clean` - Clean build artifacts and cache

**Note**: Test command only runs selected test files, not the entire test suite

### Running the Bot

- Start bot: `uv run python3 pyfibot/pyfibot.py <config.yml>`
- Install dependencies: `uv sync` or `pip install -e .`
- Docker: Available via Dockerfile

## Architecture Overview

### Core Components

- **pyfibot/pyfibot.py**: Main entry point and factory setup (PyFiBotFactory class)
- **pyfibot/botcore.py**: Core IRC bot functionality using Twisted Matrix
- **pyfibot/modules/**: Modular plugin system for bot commands and features

### Module System

The bot uses a modular architecture where features are implemented as separate modules:

- **Dynamic loading**: Modules loaded via `exec()` at runtime (pyfibot.py:235)
- **Hot reloading**: Modules can be reloaded without restart via factory.ns management
- **Discovery pattern**: `_findmodules()` finds modules by `module_*.py` naming pattern
- Each module can define commands, URL handlers, and event handlers
- **Factory pattern**: PyFiBotFactory manages multiple network connections and module lifecycle

### Configuration Architecture

- **YAML-based**: Uses PyYAML for configuration with JSON schema validation
- **Runtime reloading**: `reload_config()` method allows live config updates
- **Network abstraction**: Network class wraps connection details
- **Per-module config**: Modules access config via `bot.config.get("module_name", {})`

### Key Directories

- **pyfibot/modules/**: Active bot modules
- **pyfibot/modules/available/**: Disabled/example modules
- **pyfibot/util/**: Utility functions (URL handling, etc.)
- **tests/**: Test suite with VCR cassettes for HTTP mocking

### Configuration

- Uses YAML configuration files (see example.yml, example_full.yml)
- JSON schema validation via config_schema.json
- Supports SSL, IPv6, virtualenv, and Tor proxy

### Key Dependencies

- **Python 3.8+**: Required Python version
- **Twisted Matrix 24.0+**: Core IRC library with Python 3 support
- **PyYAML**: Configuration parsing
- **Requests**: HTTP client for URL handling
- **VCR.py**: HTTP interaction recording for tests (via cassettes/)

### Testing Strategy

- Uses pytest with custom configuration in pytest.ini
- **VCR cassettes in tests/cassettes/ for mocking HTTP responses** - critical for URL title testing
- Test configuration in test_config.yml
- **Mock bot implementation in tests/bot_mock.py** - use `BotMock` class for testing modules
- Tests focus on specific modules (openweather, pyfiurl, urltitle) rather than full coverage
- Use `VCR_RECORD_MODE=once` for recording new HTTP interactions

## Module Development

When working with modules:

- Follow existing patterns in pyfibot/modules/
- **Module files must start with `module_` prefix** (e.g., `module_example.py`)
- Modules can define command handlers, URL title fetchers, and event handlers
- Use the existing logging framework (import logging; log = logging.getLogger("modulename"))
- Test modules using the mock bot framework in tests/
- **Note**: Modules are intentionally kept untyped to maintain development simplicity. Type checking is only applied to core bot classes.

### Module Structure Patterns

**Required module structure:**
```python
# Global variables for module state
config = None
bot = None
handlers = []  # For URL handlers

def init(botref):
    """Initialize module - called when loaded/reloaded"""
    global config, bot, handlers
    bot = botref
    config = bot.config.get("module_name", {})
    # Load handlers: [(name, function), ...]
    handlers = [(h, ref) for h, ref in globals().items() if h.startswith("_handle_")]
```

**Command functions:**
- Use pattern: `def command_name(user, channel, args)` for regular commands
- Use pattern: `def admin_command(bot, user, channel, args)` for admin-only commands

**URL handlers:**
- Function name pattern: `_handle_sitename(url, bot, channel)`
- Registered automatically in `init()` using the `_handle_` prefix pattern

### Module Loading System

- Modules are loaded dynamically via `exec()` in pyfibot/pyfibot.py:235
- `_findmodules()` discovers modules by filename pattern
- Hot reloading: modules call `finalize()` function before reload if present
- Module namespace stored in factory.ns for runtime management
