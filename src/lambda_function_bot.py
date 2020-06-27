import logging
import os

from defaults import *
from wsb_reddit import WSBReddit

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_bot(event, context):
    # Use these keys for configuring the bot at runtime using events (can send test events in lambda)
    try:
        event['submission_limit']
    except KeyError:
        event['submission_limit'] = DEFAULT_SUBMISSION_RETRIEVE_LIMIT
    try:
        event['reprocess']
    except KeyError:
        event['reprocess'] = DEFAULT_REPROCESS

    logger.info(f"Running with settings: {event}")
    run(
        event['submission_limit'],
        event['reprocess']
    )
    logger.info("Finished Running")


def run(submission_limit: int, reprocess: bool):
    wsb_reddit = WSBReddit(os.environ['BotUserName'])
    submissions = wsb_reddit.get_submissions(limit=submission_limit, flair_filter=True)

    wsb_reddit.process_inbox()
    wsb_reddit.process_submissions(submissions, reprocess=reprocess)
