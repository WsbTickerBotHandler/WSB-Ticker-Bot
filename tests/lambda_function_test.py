import pytest

from lambda_function_bot import *


@pytest.mark.integration
def test_run():
    run()
