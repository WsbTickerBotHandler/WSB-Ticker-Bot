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
        num_processed = 0
        for message in self.reddit.inbox.unread():
            self.handle_message(message)
            num_processed += 1
        logger.info(f'Processed {num_processed} user messages')

    def process_submissions(self, submissions: [Submission]):
        # self.comment_on_submissions(submissions)
        self.notify_users(submissions)

    def get_submissions(self, flair_filter=False, limit=30) -> [Submission]:
        valid_flairs = {'DD', 'Fundamentals', 'Discussion'}
        # valid_flairs = {'DD'}
        subs = self.wsb.new(limit=limit)
        if flair_filter:
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
                    logger.info(f'Commenting on {submission.title}')
                    submission.reply(make_comment_from_tickers(filtered_tickers))
                self.database.add_submission_marker(COMMENTED_SUBMISSIONS_TABLE_NAME, submission.id)

    def notify_users(self, submissions: [Submission], reprocess=False):
        notifications = dict()
        tickers_with_submissions: {str: [Submission]} = self.group_submissions_for_tickers(
            submissions, reprocess=reprocess
        )
        logger.info(f'Found {len(tickers_with_submissions)} tickers')
        for ticker, subs in tickers_with_submissions.items():
            logger.info(f"Found ticker {ticker} mentioned in posts [{', '.join([s.id for s in subs ])}]")
            users_to_notify = self.database.get_users_subscribed_to_ticker(ticker)
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
        logger.info(f'Notified {len(notifications)} users about tickers')

    def handle_message(self, item: Union[Message, Comment]):
        body: str = item.body
        author: Redditor = item.author
        tickers: [str] = parse_tickers_from_text(body)

        if tickers.count() == 0 and not item.was_comment():
            logger.info(f'User {author} submitted uninterpretable message: {body}')
            notify_user_of_error(author)
        elif tickers.count() == 0 and item.was_comment():
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
                self.database.add_submission_marker(NOTIFIED_SUBMISSIONS_TABLE_NAME, submission.id)
                num_processed += 1
        logger.info(f'Processed {num_processed} new submissions')

        return tickers_submissions
