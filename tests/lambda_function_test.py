import pytest

from lambda_function_process_submissions import *


@pytest.mark.integration
def test_run():
    run()
