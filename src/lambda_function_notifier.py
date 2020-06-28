import logging
import os

from wsb_reddit import WSBReddit

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def process_notifications(event, context):
    wsb_reddit = WSBReddit(os.environ['BotUserName'])

    notifications = event['Records']
    logger.info(f"Processing {len(notifications)} notifications")
    for notification in notifications:
        wsb_reddit.notify(notification)
    logger.info("Finished processing")
