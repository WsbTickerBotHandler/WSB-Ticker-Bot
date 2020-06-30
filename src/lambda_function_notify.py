import logging
import os

from utils import generate_notification_id, decode_notification_kinesis
from wsb_reddit import WSBReddit

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_notify(event, context):
    bot_user = os.environ['BotUserName']
    wsb_reddit = WSBReddit(bot_user)

    notification_events = event['Records']
    logger.info(f"{bot_user} processing {len(notification_events)} notifications")
    for notification_record in [n['kinesis']['data'] for n in notification_events]:
        notification = decode_notification_kinesis(notification_record)
        notification_id = generate_notification_id(notification)

        has_notified = wsb_reddit.database.has_already_notified(notification_id)
        if not has_notified:
            wsb_reddit.notify(notification)
            wsb_reddit.database.add_notification_marker(notification_id)

    logger.info(f"{bot_user} finished processing")
