import pytest

from praw.models import Submission, Redditor
from wsb_reddit import WSBReddit


@pytest.fixture(scope="session")
def wsb_reddit_client():
    yield WSBReddit()


@pytest.fixture(scope="session")
def a_submission(wsb_reddit_client) -> Submission:
    yield wsb_reddit_client.reddit.submission(id='gn18pl')


@pytest.fixture(scope="session")
def a_user(wsb_reddit_client) -> Redditor:
    yield Redditor(wsb_reddit_client.reddit, name='WSBTickerBotHandler')
