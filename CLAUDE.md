# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack Guidelines

**IMPORTANT**: For general technology choices and project guidelines, refer to `/llm-shared/project_tech_stack.md` which contains the authoritative guidelines that may change over time.

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

### Running the Bot

- Start bot: `uv run python3 pyfibot/pyfibot.py <config.yml>`
- Install dependencies: `uv sync` or `pip install -e .`
- Docker: Available via Dockerfile

## Architecture Overview

### Core Components

- **pyfibot/pyfibot.py**: Main entry point and factory setup
- **pyfibot/botcore.py**: Core IRC bot functionality using Twisted Matrix
- **pyfibot/modules/**: Modular plugin system for bot commands and features

### Module System

The bot uses a modular architecture where features are implemented as separate modules:

- Modules are loaded dynamically and can be reloaded without restart
- Each module can define commands, URL handlers, and event handlers
- Module structure supports both simple functions and class-based implementations

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
- VCR cassettes in tests/cassettes/ for mocking HTTP responses
- Test configuration in test_config.yml
- Mock bot implementation in tests/bot_mock.py

## Module Development

When working with modules:

- Follow existing patterns in pyfibot/modules/
- Modules can define command handlers, URL title fetchers, and event handlers
- Use the existing logging framework (import logging; log = logging.getLogger("modulename"))
- Test modules using the mock bot framework in tests/
- **Note**: Modules are intentionally kept untyped to maintain development simplicity. Type checking is only applied to core bot classes.
