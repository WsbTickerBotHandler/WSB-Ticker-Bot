import logging
from wsb_reddit import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Notify users about 1 new DD submission per run
DEFAULT_SUBMISSION_LIMIT = 1
DEFAULT_REPROCESS = False


def lambda_handler(event, context):
    try:
        event['submission_limit']
    except KeyError:
        event['submission_limit'] = DEFAULT_SUBMISSION_LIMIT
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
    wsb_reddit = WSBReddit()
    submissions = wsb_reddit.get_submissions(limit=submission_limit, flair_filter=True)

    wsb_reddit.process_inbox()
    # wsb_reddit.process_submissions(submissions, reprocess=reprocess)
