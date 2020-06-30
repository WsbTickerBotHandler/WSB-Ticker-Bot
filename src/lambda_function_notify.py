import logging
import os

from utils import generate_notification_id, decode_notification_from_sqs
from wsb_reddit import WSBReddit

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_notify(event, context):
    bot_user = os.environ['BotUserName']
    wsb_reddit = WSBReddit(bot_user)

    records = event['Records']

    for notification_event in records:
        notifications = decode_notification_from_sqs(notification_event['body'])
        logger.info(f"{bot_user} processing one batch of {len(notifications)} notifications")
        for notification in notifications:
            notification_id = generate_notification_id(notification)
            has_notified = wsb_reddit.database.has_already_notified(notification_id)
            if not has_notified:
                wsb_reddit.notify(notification)
                wsb_reddit.database.add_notification_marker(notification_id)

    logger.info(f"{bot_user} finished processing")
