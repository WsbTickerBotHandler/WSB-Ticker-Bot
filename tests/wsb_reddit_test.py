import logging

from fixtures import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@pytest.mark.integration
def test_process_inbox(wsb_reddit_client):
    wsb_reddit_client.process_inbox()


@pytest.mark.integration
def test_process_submissions(wsb_reddit_client, a_submission):
    import time
    start_time = time.time()
    wsb_reddit_client.process_submissions([a_submission], reprocess=True)
    logger.info("--- %s seconds ---" % (time.time() - start_time))


@pytest.mark.integration
def test_get_submissions(wsb_reddit_client):
    logger.info(wsb_reddit_client.get_submissions(1))


@pytest.mark.integration
def test_comment_on_submission(wsb_reddit_client, a_submission):
    wsb_reddit_client.comment_on_submissions([a_submission], reprocess=True)


@pytest.mark.integration
def test_notify(wsb_reddit_client):
    sub1 = SubmissionNotification(id='1', link_flair_text='DD', permalink='test.permalink1', title='test-submission1')
    sub2 = SubmissionNotification(id='2', link_flair_text='DD', permalink='test.permalink2', title='test-submission1')
    sub3 = SubmissionNotification(id='3', link_flair_text='DD', permalink='test.permalink3', title='test-submission3')
    notification = {
        "SomeUser":
            [
                {
                    'ticker': '$A',
                    'subs': [sub1]
                },
                {
                    'ticker': '$B',
                    'subs': [sub1, sub2],
                },
                {
                    'ticker': '$C',
                    'subs': [sub1, sub2, sub3],
                }
            ]
    }
    wsb_reddit_client.notify(list(notification.items())[0])


@pytest.mark.integration
def test_notify_some_users_of_something(wsb_reddit_client):
    """
    Use this to send admin notifications to users
    """
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
