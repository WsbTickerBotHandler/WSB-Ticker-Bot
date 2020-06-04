import logging
from fixtures import *
from wsb_reddit_utils import get_tickers_for_submission, create_error_notification, create_subscription_notification, create_all_subscription_notification
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@pytest.mark.integration
def test_get_submissions(wsb_reddit_client):
    logger.info(wsb_reddit_client.get_submissions(1))


@pytest.mark.integration
def test_get_tickers_for_submissions(wsb_reddit_client, a_submission):
    logger.info(get_tickers_for_submission(a_submission))


@pytest.mark.integration
def test_filter_nonexistent_tickers(wsb_reddit_client):
    assert [t for t in ["asdf"] if wsb_reddit_client.database.ticker_exists(t)] == []
    assert [t for t in ["$AAPL", "$ZM"] if wsb_reddit_client.database.ticker_exists(t)] == ["$AAPL", "$ZM"]


@pytest.mark.integration
def test_process_inbox(wsb_reddit_client):
    wsb_reddit_client.process_inbox()


@pytest.mark.integration
def test_group_submissions_for_tickers(wsb_reddit_client, a_submission):
    logger.info(wsb_reddit_client.group_submissions_for_tickers([a_submission], reprocess=True))


@pytest.mark.integration
def test_comment_on_submission(wsb_reddit_client, a_submission):
    wsb_reddit_client.comment_on_submissions([a_submission], reprocess=True)


@pytest.mark.integration
def test_process_submissions(wsb_reddit_client, a_submission):
    import time
    start_time = time.time()
    wsb_reddit_client.process_submissions([a_submission], reprocess=True)
    logger.info("--- %s seconds ---" % (time.time() - start_time))


@pytest.mark.integration
def test_notify_user_of_error(a_user: Redditor):
    create_error_notification()


@pytest.mark.integration
def test_notify_user_of_subscription(a_user: Redditor):
    create_subscription_notification(["$BBWG", "$DDDD"])


@pytest.mark.integration
def test_notify_user_of_all_subscription(a_user: Redditor):
    create_all_subscription_notification()


@pytest.mark.integration
def test_notify_some_users_of_something(wsb_reddit_client):
    us = []

    def create_notification(user: str):
        try:
            wsb_reddit_client.reddit.redditor(user).message(
                'Subject',
                'Message'
            )
            logger.info(f'Notified {user}')
        except Exception as e:
            logger.error(f'Could not send {user} a message: {e}')

    [create_notification(u) for u in us]
