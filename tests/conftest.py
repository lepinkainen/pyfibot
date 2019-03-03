import os
import pytest

VCR_RECORD_MODE = os.environ.get("VCR_RECORD_MODE", "once")


def pytest_addoption(parser):
    parser.addoption(
        "--vcrmode",
        action="store",
        type="string",
        default=VCR_RECORD_MODE,
        help="set vcr record mode [once, new_episodes, none, all]",
    )


@pytest.fixture
def vcrmode(request):
    return request.config.getoption("--vcrmode")
