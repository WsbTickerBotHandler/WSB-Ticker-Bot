import pytest

from defaults import *
from praw.models import Submission, Redditor
from wsb_reddit import WSBReddit


@pytest.fixture(scope="session")
def wsb_reddit_client(notification_queue_url):
    yield WSBReddit(BOT_USERNAME, queue_url=notification_queue_url)


@pytest.fixture(scope="session")
def a_submission(wsb_reddit_client) -> Submission:
    # Personal test submission posted by /u/WSBTickerBotHandler
    yield wsb_reddit_client.reddit.submission(id='gn18pl')


@pytest.fixture(scope="session")
def a_user(wsb_reddit_client) -> Redditor:
    yield Redditor(wsb_reddit_client.reddit, name='WSBTickerBotHandler')


@pytest.fixture(scope="session")
def notification_queue_url():
    yield 'SomeSqsUrl'
