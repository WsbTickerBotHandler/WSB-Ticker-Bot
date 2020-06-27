import logging
import os

from utils import decode_notification_from_sqs
from wsb_reddit import WSBReddit

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def process_notifications(event, context):
    wsb_reddit = WSBReddit(os.environ['BotUserName'])
    notifications = event['Records']
    logger.info(f"Processing {len(notifications)} notification")
    for notification in notifications:
        wsb_reddit.notify(decode_notification_from_sqs(notification["body"]))
    logger.info("Finished processing")
