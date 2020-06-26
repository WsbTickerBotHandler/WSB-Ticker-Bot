import logging
from functools import partial
from typing import Union

from praw.models import Message, Comment, Submission, Redditor
from praw.reddit import Reddit

from database import Database, NOTIFIED_SUBMISSIONS_TABLE_NAME, COMMENTED_SUBMISSIONS_TABLE_NAME
from defaults import *
from messages import (make_comment_from_tickers,
                      reply_to, create_error_notification, create_subscription_notification,
                      create_unsubscription_notification, create_all_subscription_notification,
                      create_all_unsubscription_notification, create_user_not_old_enough)
from submission_utils import SubmissionNotification
from utils import (get_tickers_for_submission,
                   group_submissions_for_tickers, is_account_old_enough, make_pretty_message,
                   parse_tickers_from_text, create_notifications)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WSBReddit:
    def __init__(self):
        self.reddit = Reddit(BOT_USERNAME)
        self.wsb = self.reddit.subreddit(SUBREDDIT)
        self.database = Database()

    def process_inbox(self):
        """
        Respond to user instructions to the bot
        """
        num_processed = 0
        messages = list(self.reddit.inbox.unread(limit=UNREAD_MESSAGES_TO_PROCESS))
        messages.reverse()
        for message in messages:
            self.handle_message(message)
            num_processed += 1
        num_processed > 0 and logger.info(f'Processed {num_processed} user messages')

    def process_submissions(self, submissions: [Submission], reprocess=False):
        """
        Process submissions by first commenting on them (temp disabled) and then notifying users of them
        :param submissions: to process
        :param reprocess: whether to reprocess all submissions regardless of whether they have already been marked as processed
        :return:
        """
        logger.info(f'Retrieved {len(submissions)} submissions')
        # self.comment_on_submissions(submissions)
        has_already_processed_id = partial(self.database.has_already_processed, table_name=NOTIFIED_SUBMISSIONS_TABLE_NAME)
        tickers_with_submissions: {str: [SubmissionNotification]} = group_submissions_for_tickers(
            submissions, has_already_processed_id, reprocess=reprocess
        )
        self.notify_users(tickers_with_submissions)
        [self.database.add_submission_marker(NOTIFIED_SUBMISSIONS_TABLE_NAME, submission.id) for submission in submissions]
        logger.info(f'Processed {len(submissions)} submissions')

    def get_submissions(self, limit, flair_filter=False) -> [Submission]:
        """
        Retrieve submissions for the bot to work with
        :param limit: retrieve this many submissions
        :param flair_filter: for these flairs
        """
        subs = self.wsb.new(limit=limit)
        if flair_filter:
            return [s for s in subs if s.link_flair_text in VALID_FLAIRS]
        else:
            return [s for s in subs]

    def comment_on_submissions(self, submissions: [Submission], reprocess=False):
        """
        Have the bot comment on new DD submissions with links to subscribe to tickers found in the submission
        :param submissions: to comment on
        :param reprocess: whether to recomment on all submissions regardless of whether they have already been marked as commented
        """
        for submission in submissions:
            if self.database.has_already_processed(submission.id, table_name=COMMENTED_SUBMISSIONS_TABLE_NAME) and not reprocess:
                continue
            else:
                tickers = get_tickers_for_submission(submission)
                if len(tickers) != 0:
                    logger.info(f'Commenting on submission {submission.id}')
                    submission.reply(make_comment_from_tickers(tickers))
                self.database.add_submission_marker(COMMENTED_SUBMISSIONS_TABLE_NAME, submission.id)

    def notify_users(self, tickers_with_submissions: {str: [SubmissionNotification]}):
        """
        Notify users for a number of tickers which have been found and which submissions they were found within
        :param tickers_with_submissions: map of ticker -> submissions found in
        """
        get_users_subscribed_to_ticker = partial(self.database.get_users_subscribed_to_ticker)
        notifications = create_notifications(tickers_with_submissions, get_users_subscribed_to_ticker)
        for n in notifications:
            self.notify(n)

        len(notifications) > 0 and logger.info(f'Notified {len(notifications)} users')

    def notify(self, notification):
        user_to_notify, notify_about_these_subs = notification
        try:
            self.reddit.redditor(user_to_notify).message(
                'New DD posted!',
                make_pretty_message(notify_about_these_subs)
            )
        except Exception as e:
            logger.error(f'Notification of user {user_to_notify} ran into an error: {e}')

    def handle_message(self, item: Union[Message, Comment]):
        """
        Respond to a particular user message or comment
        :param item: the message or comment to respond to
        """
        body: str = item.body
        author: Redditor = item.author

        if author.name in {"reddit", "AutoModerator"}:
            item.mark_read()
            return
        tickers = [ticker for ticker in parse_tickers_from_text(body)]

        is_old_enough = is_account_old_enough(author)

        if len(tickers) > MAX_TICKERS_TO_SUBSCRIBE_AT_ONCE and is_old_enough:
            logger.info(f'User {author} requested subscription to more than {MAX_TICKERS_TO_SUBSCRIBE_AT_ONCE} tickers')
            reply_to(item, "You can only subscribe to 10 tickers at once")
        elif body.lower() == "all dd" and is_old_enough:
            self.database.subscribe_user_to_all_dd_feed(author.name)
            logger.info(f'User {author} requested subscription to all DD')
            reply_to(item, create_all_subscription_notification())
        elif body.lower() == "stop all" and is_old_enough:
            logger.info(f'User {author} requested unsubscription from all DD')
            self.database.unsubscribe_user_from_all_dd_feed(author.name)
            reply_to(item, create_all_unsubscription_notification())
        elif len(tickers) == 0 and not item.was_comment and is_old_enough:
            logger.info(f'User {author} submitted uninterpretable message: {body}')
            reply_to(item, create_error_notification())
        elif len(tickers) == 0 and item.was_comment:
            item.mark_read()
            return
        elif body.lower().startswith("stop"):
            logger.info(f'User {author} requested unsubscription from {tickers}')
            [self.database.unsubscribe_user_from_ticker(author.name, ticker) for ticker in tickers]
            reply_to(item, create_unsubscription_notification(tickers))
        elif is_old_enough:
            logger.info(f'User {author} requested subscription to {tickers}')
            [self.database.subscribe_user_to_ticker(author.name, ticker) for ticker in tickers]
            reply_to(item, create_subscription_notification(tickers))
        else:
            logger.info(f'User {author} has an account which is not old enough to use the bot')
            reply_to(item, create_user_not_old_enough())

        item.mark_read()
