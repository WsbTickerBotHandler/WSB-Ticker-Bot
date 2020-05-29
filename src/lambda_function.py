from wsb_reddit import *

logger = getLogger()


def lambda_handler(event, context):
    logger.info(f"Running... {event}")
    run()
    logger.info("Finished Running")


def run():

    wsb_reddit = WSBReddit()
    submissions = wsb_reddit.get_submissions()

    wsb_reddit.process_inbox()
    wsb_reddit.process_submissions(submissions)
