# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack Guidelines

**IMPORTANT**: For general technology choices and project guidelines, refer to `/llm-shared/project_tech_stack.md` which contains the authoritative guidelines that may change over time. The `llm-shared/` directory is a git submodule.

## Development Commands

In general don't try to run `python3` directly, use the `uv run` command instead. This ensures that the correct Python environment is used and dependencies are managed properly.

### Available Tasks

- `task test` - Run tests with coverage
- `task test-ci` - Run tests in CI environment
- `task lint` - Run flake8 linting
- `task typecheck` - Run mypy type checking on core files only
- `task format` - Format code with black
- `task format-check` - Check if code is formatted correctly
- `task build` - Build the project (runs tests, lint, and typecheck)
- `task dev-install` - Install with development dependencies
- `task clean` - Clean build artifacts and cache

### Running a Single Test

```bash
uv run pytest tests/test_urltitle_simple.py -v              # single file
uv run pytest tests/test_urltitle_simple.py::test_get_views  # single test function
```

**Note**: Only specific test files are wired into `task test` (see Taskfile.yml). Some test files (e.g. test_openweather.py) have all tests commented out. When adding tests, ensure they are added to the Taskfile test command if they should run in CI.

### Running the Bot

- Start bot: `uv run python3 pyfibot/pyfibot.py <config.yml>`
- Install dependencies: `uv sync` or `pip install -e .`
- Docker: Available via Dockerfile

## Architecture Overview

### Core Components

- **pyfibot/pyfibot.py**: `PyFiBotFactory` (Twisted factory) — parses config, manages networks, loads/reloads modules dynamically via `_loadmodules()`. Stores module namespaces in `self.ns`.
- **pyfibot/botcore.py**: `CoreCommands` mixin and `PyFiBot` (Twisted IRC protocol) — handles IRC events, command dispatch, URL detection. Commands are dispatched by looking for `command_<name>` and `admin_<name>` functions across all loaded module namespaces.
- **pyfibot/modules/**: Plugin modules, loaded at runtime. Files in `available/` are disabled.

### Module Conventions

Modules are plain Python files named `module_<name>.py`. Key function signatures the bot looks for:

- `command_<name>(bot, user, channel, args)` — triggered by `!<name>` in IRC
- `admin_<name>(bot, user, channel, args)` — admin-only commands
- `init(botref)` — called when module is loaded; used to store bot/config references
- `finalize()` — called before module is unloaded/reloaded
- `_handle_<pattern>(url)` — URL handlers in module_urltitle (prefixed with `_handle_`)

Modules are intentionally kept untyped. Type checking (`task typecheck`) only applies to `botcore.py` and `pyfibot.py`.

### Import Paths

The bot runs with `pyfibot/` on `sys.path`, so modules use bare imports: `from util import pyfiurl`, `import botcore`. This is **not** standard package-relative import style.

### Testing

- Uses pytest with VCR cassettes in `tests/cassettes/` for HTTP mocking
- `tests/bot_mock.py` provides `BotMock` and `FactoryMock` — lightweight stand-ins that avoid Twisted reactor. `BotMock.say()` returns `(channel, message)` tuples for assertion.
- Test config in `tests/test_config.yml`; if a `config.yml` exists at repo root, the mock factory uses that instead.

### Configuration

- YAML config files (see `example.yml`, `example_full.yml`)
- JSON schema validation via `config_schema.json`
- Module-specific config accessed via `bot.config.get("module_<name>", {})`
