import logging
import os

from wsb_reddit import WSBReddit

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_notify(event, context):
    bot_user = os.environ['BotUserName']
    wsb_reddit = WSBReddit(bot_user)

    notifications = event['Records']
    logger.info(f"{bot_user} processing {len(notifications)} notifications")
    for notification in notifications:
        wsb_reddit.notify(notification)
    logger.info(f"{bot_user} finished processing")
