from typing import Union
import time
import logging
import concurrent.futures
from itertools import islice
from database import Database, NOTIFIED_SUBMISSIONS_TABLE_NAME, COMMENTED_SUBMISSIONS_TABLE_NAME
from wsb_reddit_utils import *
from praw.reddit import Reddit
from praw.models import Message, Comment
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
        for message in self.reddit.inbox.unread(limit=50):
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
            return [s for s in subs if s.link_flair_text in valid_flairs and len(s.selftext) > 300]
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

        logger.debug(f'Notifications object: {notifications}')

        def chunks(data, size=60):
            it = iter(data)
            for i in range(0, len(data), size):
                yield {k: data[k] for k in islice(it, size)}

        def notify(notification):
            try:
                user_to_notify, notify_about_these_subs = notification
                self.get_another_reddit_instance().redditor(user_to_notify).message(
                    'New DD posted!',
                    make_pretty_message(notify_about_these_subs)
                )
            except Exception as e:
                logger.error(f'Notification of user {users_to_notify} ran into an error: {e}')

        for chunk in chunks(notifications):
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                executor.map(notify, chunk.items())
            time_taken = (time.time() - start_time)
            sleep_for = 61 - time_taken
            logger.info(f'Took {int(time_taken)} seconds to notify 50 users, sleeping for {sleep_for} seconds')
            # Reddit limits us to 60 requests/min so wait 1 min before making 50 more requests
            time.sleep(sleep_for)

        len(notifications) > 0 and logger.info(f'Notified {len(notifications)} users about {len(notified_tickers)} tickers')

    def handle_message(self, item: Union[Message, Comment]):
        body: str = item.body
        author: Redditor = item.author
        tickers: [str] = parse_tickers_from_text(body)

        if body.lower() == "all dd":
            self.database.subscribe_user_to_all_dd_feed(author.name)
            logger.info(f'User {author} requested subscription to all DD')
            notify_user_of_all_subscription(author)
        elif body.lower() == "stop all":
            logger.info(f'User {author} requested unsubscription from all DD')
            self.database.unsubscribe_user_from_all_dd_feed(author.name)
            notify_user_of_all_unsubscription(author)
        elif len(tickers) == 0 and not item.was_comment:
            logger.info(f'User {author} submitted uninterpretable message: {body}')
            notify_user_of_error(author)
        elif len(tickers) == 0 and item.was_comment:
            item.mark_read()
            return
        elif body.lower().startswith("stop"):
            logger.info(f'User {author} requested unsubscription from {tickers}')
            [self.database.unsubscribe_user_from_ticker(author.name, ticker) for ticker in tickers]
            notify_user_of_unsubscription(author, tickers)
        else:
            logger.info(f'User {author} requested subscription to {tickers}')
            [self.database.subscribe_user_to_ticker(author.name, ticker) for ticker in tickers]
            notify_user_of_subscription(author, tickers)

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
