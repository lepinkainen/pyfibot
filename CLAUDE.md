# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**MIGRATED TO PYTHON 3** - This IRC bot has been successfully migrated from Python 2.x to Python 3.8+. All core functionality including the critical `.rehash` command works with Python 3 and modern Twisted Matrix.

## Development Commands

### Testing

- Run tests: `python3 -m pytest` or `./test.sh`
- Coverage with VCR recording: `VCR_RECORD_MODE=once coverage run --source pyfibot -m pytest`

### Linting

- Run linting: `make test` (runs flake8 with project-specific ignore rules)
- Flake8 directly: `flake8 --ignore=E501,E722,W503,E203,F821 pyfibot/`

### Running the Bot

- Start bot: `python3 pyfibot/pyfibot.py <config.yml>`
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

### Dependencies

- **Python 3.8+**: Required Python version
- **Twisted Matrix 24.0+**: Core IRC library with Python 3 support
- **PyYAML**: Configuration parsing
- **Requests**: HTTP client for URL handling
- **VCR.py**: HTTP interaction recording for tests (via cassettes/)
- **uv**: Modern Python package manager (recommended)

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
