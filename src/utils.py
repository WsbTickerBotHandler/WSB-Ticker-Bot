import logging
import re
from datetime import datetime, timedelta
from itertools import islice

from praw.models import Redditor, Submission
from praw.reddit import Reddit

from defaults import BOT_USERNAME, DEFAULT_ACCOUNT_AGE, MAX_TICKERS_ALLOWED_IN_SUBMISSION, TICKER_EXCLUSIONS
from messages import make_pretty_message
from stock_data.tickers import tickers as tickers_set
from submission_utils import SubmissionNotification

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def chunks(data, size):
    """
    Chunk a dictionary into a list of smaller dictionaries
    Useful when the notifications data is a large dict of users mapped to their notifications and we only want
    to notify a certain number of users at once
    """
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


def create_notifications(tickers_with_submissions: {str: [SubmissionNotification]}, get_users_subscribed_to_ticker):
    """
    Return all notifications each user in the form
    {'user': [
        {'ticker': 'ticker1', 'subs': [submissions]},
        {'ticker': 'ticker2', 'subs': [submissions]}
    ]}
    """
    notifications = dict()
    notified_tickers = set()
    users_subscribed_to_all: [str] = []
    # users_subscribed_to_all: [str] = self.database.get_users_subscribed_to_all_dd_feed()

    len(tickers_with_submissions) > 0 and logger.info(f'Found tickers {tickers_with_submissions.keys()} ({len(tickers_with_submissions)})')
    for ticker, subs in tickers_with_submissions.items():
        logger.info(f"Found ticker {ticker} mentioned in posts [{', '.join([s.id for s in subs])}]")
        users_to_notify = get_users_subscribed_to_ticker(ticker)
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
    sorted_notifications = {k: v for k, v in sorted(notifications.items(), key=lambda x: len(x), reverse=True)}
    logger.debug(f'Notifications object: {sorted_notifications}')
    logger.info(f"Will notify users about a total of {notified_tickers} unique tickers")
    return sorted_notifications


def get_tickers_for_submission(submission: Submission) -> [str]:
    """
    :param submission: to search for tickers
    :return: the tickers found in the title and body of the submission
    """
    logger.debug(submission.title + "\n" + (submission.selftext if submission.is_self else "LINK POST\n"))
    tickers = parse_tickers_from_text(submission.title + "\n" + ((submission.selftext + "\n") if submission.is_self else "\n"))
    # A post might spam capital words, so if we detect more than 10 tickers, don't return it
    if len(tickers) <= MAX_TICKERS_ALLOWED_IN_SUBMISSION or submission.link_flair_text == 'DD':
        return [t.upper() for t in tickers if len(t) != 0]
    else:
        logger.warning(f'Submission {submission.id} has more than {MAX_TICKERS_ALLOWED_IN_SUBMISSION} and is being excluded from processing')
        return []


def get_another_reddit_instance():
    return Reddit(BOT_USERNAME)


def group_submissions_for_tickers(submissions: [Submission], has_already_processed_id, reprocess=False) -> {str: [SubmissionNotification]}:
    """
    :param submissions: to group into tickers
    :param has_already_processed_id: a function taking a submission id and returning whether it has been processed already
    :param reprocess: override to reprocess a submission regardless of what @has_already_processed_id returns
    :return: individual tickers mapped to the submissions which mention them
    """
    tickers_submissions = dict()
    num_processed = 0
    for s in submissions:
        # todo: move submission processing flagging to outer scope
        if has_already_processed_id(s.id) and not reprocess:
            continue
        else:
            for ticker in get_tickers_for_submission(s):
                if ticker in tickers_submissions:
                    tickers_submissions[ticker].append(SubmissionNotification(s.id, s.link_flair_text, s.permalink, s.title))
                else:
                    tickers_submissions[ticker] = [SubmissionNotification(s.id, s.link_flair_text, s.permalink, s.title)]
            num_processed += 1
    logger.info(f'Grabbed {num_processed} new submissions')

    return tickers_submissions


def is_account_old_enough(account: Redditor, days: int = DEFAULT_ACCOUNT_AGE) -> bool:
    """
    :return: true if the account is older than @days, else false
    """
    created_at = datetime.utcfromtimestamp(account.created_utc)
    now = datetime.utcnow()
    return now - created_at > timedelta(days=days)


def notify(notification):
    user_to_notify, notify_about_these_subs = notification
    try:
        get_another_reddit_instance().redditor(user_to_notify).message(
            'New DD posted!',
            make_pretty_message(notify_about_these_subs)
        )
    except Exception as e:
        logger.error(f'Notification of user {user_to_notify} ran into an error: {e}')


def parse_tickers_from_text(text) -> [str]:
    """
    :return: all tickers found in the text string
    """
    punct_chars = """-.%#,:;'"&/![]()?"""
    # Won't match LULU\ yet
    punct_regex = r"(?:[-.%#,:;'\"&/!\[\]\(\)\?]*)"
    three_5 = r'{3,5}'
    one_2 = r'{1,2}'
    one_5 = r'{1,5}'
    one = r'{1}'
    match_3_5_maybe_with_dollar = fr'\$?[A-Z]{three_5}(?:\.[A-Z]{one})?{punct_regex}(?=\s|$|/)'
    match_1_5_lowercase_with_dollar = fr'\$[A-Za-z]{one_5}(?:\.[A-Za-z]{one})?{punct_regex}(?=\s|$|/)'
    match_1_2_with_dollar = fr'\$[A-Za-z]{one_2}(?:\.[A-Za-z]{one})?{punct_regex}(?=\s|$|/)'
    ticker_regex = f"{match_3_5_maybe_with_dollar}|{match_1_5_lowercase_with_dollar}|{match_1_2_with_dollar}"

    raw_tickers = [t.upper() for t in re.findall(ticker_regex, text)]

    # Remove matched punctuation on the ends of tickers
    stripped_punct_tickers = [t.strip(punct_chars) for t in raw_tickers]

    # Exclude some common terms which we know are not tickers
    for exclusion in TICKER_EXCLUSIONS:
        while exclusion in stripped_punct_tickers:
            stripped_punct_tickers.remove(exclusion)

    # Add $ to front if it is not there, unique, and sort
    return list(sorted(set(['$' + ticker if ticker[0] != '$' else ticker for ticker in stripped_punct_tickers if ticker.strip('$') in tickers_set])))
