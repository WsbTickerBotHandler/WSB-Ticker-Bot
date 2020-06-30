import pytest
from praw.models import Submission, Redditor

from defaults import *
from submission_utils import SubmissionNotification
from wsb_reddit import WSBReddit


@pytest.fixture(scope="session")
def wsb_reddit_client(notification_stream_name):
    yield WSBReddit(BOT_USERNAME, queue_url="SOME_QUEUE_URL")


@pytest.fixture(scope="session")
def a_submission(wsb_reddit_client) -> Submission:
    # Personal test submission posted by /u/WSBTickerBotHandler
    yield wsb_reddit_client.reddit.submission(id='gn18pl')


@pytest.fixture(scope="session")
def a_user(wsb_reddit_client) -> Redditor:
    yield Redditor(wsb_reddit_client.reddit, name='WSBTickerBotHandler')


@pytest.fixture(scope="session")
def notification_stream_name():
    yield 'wsb-ticker-bot-notifications'


@pytest.fixture(scope="session")
def notifications():
    yield [
        {'User0': [
            {
                'subs': [SubmissionNotification(
                    id='gn18pl',
                    link_flair_text=None,
                    permalink='/r/test/comments/gn18pl/check_it_out/',
                    title='Check it out'
                )],
            'ticker': '$SPY'
            }
        ]},
        {'User1': [{
            'subs': [SubmissionNotification(
                id='gn18pl',
                link_flair_text=None,
                permalink='/r/test/comments/gn18pl/check_it_out/',
                title='Check it out'
            )],
            'ticker': '$SPXL'
        }]}
    ]


@pytest.fixture(scope="session")
def notification_kinesis():
    yield (
        'SomeUser',
        [{'ticker': '$SPY',
          'subs': [SubmissionNotification(id='gn18pl', link_flair_text='DD', permalink='/r/test/comments/gn18pl/check_it_out/', title='Check it out')]}]
    )
