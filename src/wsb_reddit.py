from typing import Union
import logging
from database import *
from wsb_reddit_utils import *
from praw.reddit import Reddit
from praw.models import *
from stock_data.tickers import tickers as tickers_set

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WSBReddit:
    def __init__(self):
        self.reddit = Reddit("WSBStockTickerBot")
        self.wsb = self.reddit.subreddit("wallstreetbets")
        self.database = Database()

    def process_inbox(self):
        messages = self.reddit.inbox.unread()
        for message in messages:
            self.handle_message(message)

    def process_submissions(self, submissions: [Submission]):
        # self.comment_on_submissions(submissions)
        self.notify_users(submissions)

    def get_submissions(self, flair_filter=False, limit=30) -> [Submission]:
        valid_flairs = {'DD', 'Fundamentals', 'Stocks', 'Discussion'}
        if flair_filter:
            return [s for s in self.wsb.rising(limit=limit) if s.link_flair_text in valid_flairs]
        else:
            return [s for s in self.wsb.rising(limit=limit)]

    def comment_on_submissions(self, submissions: [Submission], reprocess=False):
        for submission in submissions:
            if self.database.has_already_processed(COMMENTED_SUBMISSIONS_TABLE_NAME, submission.id) and not reprocess:
                continue
            else:
                tickers = get_tickers_for_submission(submission)
                filtered_tickers = [ticker for ticker in tickers if ticker.strip('$') in tickers_set]
                if len(filtered_tickers) != 0:
                    logger.info(f'Commenting on {submission.title}')
                    submission.reply(make_comment_from_tickers(filtered_tickers))
                self.database.add_submission_marker(COMMENTED_SUBMISSIONS_TABLE_NAME, submission.id)

    def notify_users(self, submissions: [Submission], reprocess=False):
        notifications = dict()
        tickers_with_submissions: {str: {(str, str)}} = self.group_submissions_for_tickers(
            submissions, reprocess=reprocess
        )
        for ticker, subs in tickers_with_submissions.items():
            logger.info(f'Found ticker {ticker} mentioned in posts {subs}')
            users_to_notify = self.database.get_users_subscribed_to_ticker(ticker)
            logger.debug(f'Users subscribed to {ticker} were {users_to_notify}')
            for u in users_to_notify:
                if u in notifications:
                    notifications[u].append({ticker: subs})
                else:
                    notifications[u] = [{ticker: subs}]

        for u, ticker_notifications in notifications.items():
            self.reddit.redditor(u).message(
                'New DD posted!',
                make_pretty_message(ticker_notifications)
            )
            logger.info(f'Notified {u} about tickers {ticker_notifications}')

    def handle_message(self, item: Union[Message, Comment]):
        body: str = item.body
        author: Redditor = item.author
        tickers = parse_tickers_from_text(body)

        if body.lower().startswith("stop"):
            logger.info(f'User {author} requested unsubscription from {tickers}')
            [self.database.unsubscribe_user_from_ticker(author.name, ticker) for ticker in tickers]
            notify_user_of_unsubscription(author, tickers)
        else:
            logger.info(f'User {author} requested subscription to {tickers}')
            [self.database.subscribe_user_to_ticker(author.name, ticker) for ticker in tickers]
            notify_user_of_subscription(author, tickers)

        item.mark_read()

    def group_submissions_for_tickers(self, submissions: [Submission], reprocess=False) -> {str: {(str, str)}}:
        tickers_submissions = dict()
        for submission in submissions:
            # todo: move submission processing flagging to outer scope
            if self.database.has_already_processed(NOTIFIED_SUBMISSIONS_TABLE_NAME, submission.id) and not reprocess:
                continue
            else:
                tickers = get_tickers_for_submission(submission)
                logger.info(tickers)
                filtered_tickers = [ticker for ticker in tickers if ticker.strip('$') in tickers_set]
                logger.info(filtered_tickers)
                for ticker in filtered_tickers:
                    if ticker in tickers_submissions:
                        logger.debug(f'Adding {submission.permalink} to ticker {ticker}')
                        tickers_submissions[ticker].append((submission.title, submission.permalink))
                    else:
                        logger.debug(f'Ticker {ticker} not seen before. Adding with permalink {submission.permalink}')
                        tickers_submissions[ticker] = [(submission.title, submission.permalink)]
                self.database.add_submission_marker(NOTIFIED_SUBMISSIONS_TABLE_NAME, submission.id)

        return tickers_submissions
