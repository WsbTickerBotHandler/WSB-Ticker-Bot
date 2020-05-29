import pytest

from lambda_function import *


@pytest.mark.integration
def test_run():
    run()
