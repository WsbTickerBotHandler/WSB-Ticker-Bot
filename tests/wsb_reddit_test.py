import logging
from fixtures import *
from wsb_reddit_utils import get_tickers_for_submission

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@pytest.mark.integration
def test_get_submissions(wsb_reddit_client):
    logger.info(wsb_reddit_client.get_submissions(1))


@pytest.mark.integration
def test_get_tickers_for_submissions(wsb_reddit_client):
    submissions = wsb_reddit_client.get_submissions(5)
    [logger.info((s.id, get_tickers_for_submission(s))) for s in submissions]


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
