import pytest

from wsb_reddit import *


@pytest.fixture(scope="session")
def wsb_reddit_client():
    yield WSBReddit()


@pytest.fixture(scope="session")
def a_submission(wsb_reddit_client) -> Submission:
    yield wsb_reddit_client.reddit.submission(id='gn18pl')
