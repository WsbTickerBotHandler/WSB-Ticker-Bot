import pytest

from praw.models import Submission, Redditor
from wsb_reddit import WSBReddit


@pytest.fixture(scope="session")
def wsb_reddit_client():
    yield WSBReddit()


@pytest.fixture(scope="session")
def a_submission(wsb_reddit_client) -> Submission:
    # Personal test submission
    # yield wsb_reddit_client.reddit.submission(id='gn18pl')
    # A DD submission with a few tickers mentioned
    yield wsb_reddit_client.reddit.submission(id='guwpiv')


@pytest.fixture(scope="session")
def a_user(wsb_reddit_client) -> Redditor:
    yield Redditor(wsb_reddit_client.reddit, name='WSBTickerBotHandler')
