import re
import logging

from praw.models import Redditor, Submission

logger = logging.getLogger()

MAX_TICKERS = 10
# These will be excluded unless there is a $ before them
TICKER_EXCLUSIONS = ["OTM", "ITM", "ATM", "ATH", "MACD", "ROI", "GAIN", "LOSS", "TLDR", "CEO", "WSB", "EOD", "YTD",
                     "LLC", "IMO", "CEO", "CFO", "FBI", "SEC", "THE", "NYSE", "USA", "IMF", "AND", "BABY", "EST", "PDT",
                     "IPO", "YOLO"
                     ]


def parse_tickers_from_text(text) -> [str]:
    match_3_5_maybe_with_dollar = r'\$?[A-Z]{3,5}(?:\.[A-Z]{1})?(?=\s|$)'
    match_1_5_lowercase_with_dollar = r'\$[A-Za-z]{1,5}(?:\.[A-Za-z]{1})?(?=\s|$)'
    match_1_2_with_dollar = r'\$[A-Za-z]{1,2}(?:\.[A-Za-z]{1})?(?=\s|$)'
    match_spy = r'\$?SPY|\$?SPX'
    ticker_regex = f"{match_3_5_maybe_with_dollar}|{match_1_5_lowercase_with_dollar}|{match_1_2_with_dollar}|{match_spy}"

    raw_tickers = [t for t in re.findall(ticker_regex, text)]

    # Exclude some common terms which we know are not tickers
    for exclusion in TICKER_EXCLUSIONS:
        while exclusion in raw_tickers:
            raw_tickers.remove(exclusion)

    # Add $ to front if it is not there, unique, and sort
    return list(sorted(set(['$' + ticker if ticker[0] != '$' else ticker for ticker in raw_tickers])))


def get_tickers_for_submission(submission: Submission) -> [str]:
    logger.debug(submission.title + "\n" + (submission.selftext if submission.is_self else "LINK POST\n"))
    tickers = parse_tickers_from_text(submission.title + "\n" + ((submission.selftext + "\n") if submission.is_self else "\n"))
    # A post might spam capital words, so if we detect more than 10 tickers, don't return it
    if len(tickers) <= MAX_TICKERS:
        return [t.upper() for t in tickers if len(t) != 0]
    else:
        logger.warning(f'Submission {submission.id} has more than {MAX_TICKERS} and is being excluded from processing')
        return []


def group_submissions_for_tickers(submissions: [Submission]) -> {str: {Submission}}:
    tickers_submissions = {}
    for submission in submissions:
        tickers = get_tickers_for_submission(submission)
        for ticker in tickers:
            if ticker in tickers_submissions:
                tickers_submissions[ticker].add(submission)
            else:
                tickers_submissions[ticker] = {submission}
    return tickers_submissions


def notify_user_of_subscription(u: Redditor, tickers: [str]):
    u.message(
        f'I\'ve subscribed you to DD posts',
        f'You\'ll be notified when RISING DD is posted for {",".join(tickers)}\n' +
        'To stop subscriptions, send me a message like \"stop $MSFT $AAPL\"'
    )


def make_comment_from_tickers(tickers: [str]):
    return (
        "I'm a bot, REEEEEEEEEEE\n\n"
        f"I've identified these tickers in this submission: {', '.join(tickers)}\n\n"
        "To be notified of future DD posts that include a particular ticker comment "
        "with the ticker names and I'll message you when a DD post about that ticker is rising.\n\n"
        "Example: $TSLA $AAPL"
    )


def make_pretty_message(ticker_notifications: [{str: [(str, str)]}]) -> str:
    def make_title_links(submissions):
        title_links = ""
        for title, link in submissions:
            title_links += f'- [{title}]({link})\n'
        return title_links

    pretty_message = ""
    for n in ticker_notifications:
        for ticker, subs in n.items():
            pretty_message += f'##{ticker}:\n{make_title_links(subs)}'
    return pretty_message
