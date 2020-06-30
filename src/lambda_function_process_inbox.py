import logging
import os

from wsb_reddit import WSBReddit

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_process_inbox(event, context):
    wsb_reddit = WSBReddit(os.environ['BotUserName'])
    wsb_reddit.process_inbox()
