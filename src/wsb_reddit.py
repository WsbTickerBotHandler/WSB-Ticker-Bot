from typing import Union
import time
import logging

from concurrent.futures import ThreadPoolExecutor

from database import Database, NOTIFIED_SUBMISSIONS_TABLE_NAME, COMMENTED_SUBMISSIONS_TABLE_NAME
from wsb_reddit_utils import (make_pretty_message, chunks, get_tickers_for_submission, make_comment_from_tickers,
                              reply_to, parse_tickers_from_text, create_error_notification,
                              create_subscription_notification, create_unsubscription_notification,
                              create_all_subscription_notification, create_all_unsubscription_notification,
                              is_account_old_enough, create_user_not_old_enough)
from praw.reddit import Reddit
from praw.models import Message, Comment, Submission, Redditor
from stock_data.tickers import tickers as tickers_set

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WSBReddit:
    def __init__(self):
        self.reddit = Reddit("WSBStockTickerBot")
        self.wsb = self.reddit.subreddit("wallstreetbets")
        self.database = Database()

    @staticmethod
    def get_another_reddit_instance():
        return Reddit("WSBStockTickerBot")

    def process_inbox(self):
        num_processed = 0
        messages = list(self.reddit.inbox.unread(limit=50))
        messages.reverse()
        for message in messages:
            self.handle_message(message)
            num_processed += 1
        num_processed > 0 and logger.info(f'Processed {num_processed} user messages')

    def process_submissions(self, submissions: [Submission], reprocess=False):
        # self.comment_on_submissions(submissions)
        logger.info(f'Retrieved {len(submissions)} submissions')
        tickers_with_submissions: {str: [Submission]} = self.group_submissions_for_tickers(
            submissions, reprocess=reprocess
        )
        self.notify_users(tickers_with_submissions)
        [self.database.add_submission_marker(NOTIFIED_SUBMISSIONS_TABLE_NAME, submission.id) for submission in submissions]
        logger.info(f'Processed {len(submissions)} submissions')

    def get_submissions(self, limit, flair_filter=False) -> [Submission]:
        # valid_flairs = {'DD', 'Discussion', 'Fundamentals'}
        valid_flairs = {'DD'}
        subs = self.wsb.new(limit=limit)
        if flair_filter:
            # return [s for s in subs if s.link_flair_text in valid_flairs and len(s.selftext) > 100]
            return [s for s in subs if s.link_flair_text in valid_flairs]
        else:
            return [s for s in subs]

    def comment_on_submissions(self, submissions: [Submission], reprocess=False):
        for submission in submissions:
            if self.database.has_already_processed(COMMENTED_SUBMISSIONS_TABLE_NAME, submission.id) and not reprocess:
                continue
            else:
                tickers = get_tickers_for_submission(submission)
                filtered_tickers = [ticker for ticker in tickers if ticker.strip('$') in tickers_set]
                if len(filtered_tickers) != 0:
                    logger.info(f'Commenting on submission {submission.id}')
                    submission.reply(make_comment_from_tickers(filtered_tickers))
                self.database.add_submission_marker(COMMENTED_SUBMISSIONS_TABLE_NAME, submission.id)

    def notify_users(self, tickers_with_submissions: {str: [Submission]}):
        MAX_USERS_TO_NOTIFY_PER_CHUNK = 60
        notifications = dict()
        notified_tickers = set()
        users_subscribed_to_all: [str] = []
        # users_subscribed_to_all: [str] = self.database.get_users_subscribed_to_all_dd_feed()

        len(tickers_with_submissions) > 0 and logger.info(f'Found tickers {tickers_with_submissions.keys()} ({len(tickers_with_submissions)})')
        for ticker, subs in tickers_with_submissions.items():
            logger.info(f"Found ticker {ticker} mentioned in posts [{', '.join([s.id for s in subs ])}]")
            users_to_notify = self.database.get_users_subscribed_to_ticker(ticker)
            unique_users_to_notify = set(users_subscribed_to_all + users_to_notify)
            if len(unique_users_to_notify) > 0:
                logger.info(f'Will notify {len(unique_users_to_notify)} users about ticker {ticker}')
                notified_tickers.add(ticker)
            for u in users_subscribed_to_all:
                if u in notifications:
                    for s in subs:
                        if s.link_flair_text == 'DD':
                            notifications[u].append({'ticker': ticker, 'subs': subs})
                else:
                    for s in subs:
                        if s.link_flair_text == 'DD':
                            notifications[u] = [{'ticker': ticker, 'subs': subs}]

            for u in users_to_notify:
                if u in notifications:
                    notifications[u].append({'ticker': ticker, 'subs': subs})
                else:
                    notifications[u] = [{'ticker': ticker, 'subs': subs}]

        # Ensure there are no duplicates in a user's notifications from the all DD subscription +
        # an individual subscription
        for u, notify_about_these in notifications.items():
            notifications[u] = list({v['ticker']: v for v in notify_about_these}.values())
        # Process largest notifications first so it fails if it can't be done
        sorted_notification = {k: v for k, v in sorted(notifications.items(), key=lambda x: len(x), reverse=True)}
        logger.debug(f'Notifications object: {sorted_notification}')

        def notify(notification):
            user_to_notify, notify_about_these_subs = notification
            try:
                self.get_another_reddit_instance().redditor(user_to_notify).message(
                    'New DD posted!',
                    make_pretty_message(notify_about_these_subs)
                )
            except Exception as e:
                logger.error(f'Notification of user {user_to_notify} ran into an error: {e}')

        chunked_notifications = list(chunks(sorted_notification, size=MAX_USERS_TO_NOTIFY_PER_CHUNK))
        remaining_chunks_to_process = len(chunked_notifications)
        for chunk in chunked_notifications:
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=6) as executor:
                executor.map(notify, chunk.items())
            time_taken = (time.time() - start_time)
            sleep_for = 61 - time_taken

            remaining_chunks_to_process -= 1
            # logger.info(f'Took {int(time_taken)} seconds to notify {len(chunk.items())} users, {remaining_chunks_to_process} chunks of users left to process')
            # Reddit limits us to 60 requests/min so wait 1 min before making 60 more requests
            if remaining_chunks_to_process > 0:
                logger.info(f'Took {int(time_taken)} seconds to notify {len(chunk.items())} users. Sleeping for {int(sleep_for)} seconds...')
                time.sleep(sleep_for)
            else:
                logger.info(f'Took {int(time_taken)} seconds to notify {len(chunk.items())} users')

        len(sorted_notification) > 0 and logger.info(f'Notified {len(sorted_notification)} users about {len(notified_tickers)} tickers')

    def handle_message(self, item: Union[Message, Comment]):
        MAX_TICKERS_TO_SUBSCRIBE_AT_ONCE = 10
        body: str = item.body
        author: Redditor = item.author

        if author.name == "reddit":
            item.mark_read()
            return
        tickers = [ticker for ticker in parse_tickers_from_text(body) if ticker.strip('$') in tickers_set]

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

    def group_submissions_for_tickers(self, submissions: [Submission], reprocess=False) -> {str: [Submission]}:
        tickers_submissions = dict()
        num_processed = 0
        for submission in submissions:
            # todo: move submission processing flagging to outer scope
            if self.database.has_already_processed(NOTIFIED_SUBMISSIONS_TABLE_NAME, submission.id) and not reprocess:
                continue
            else:
                tickers = get_tickers_for_submission(submission)
                filtered_tickers = [ticker for ticker in tickers if ticker.strip('$') in tickers_set]
                for ticker in filtered_tickers:
                    if ticker in tickers_submissions:
                        tickers_submissions[ticker].append((submission.title, submission.permalink))
                    else:
                        tickers_submissions[ticker] = [submission]
                num_processed += 1
        logger.info(f'Grabbed {num_processed} new submissions')

        return tickers_submissions
