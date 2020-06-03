import re
from typing import Union
from praw.models import Message, Comment
import os
from itertools import islice
import logging
import urllib.parse
import random

from praw.models import Redditor, Submission
from stock_data.tickers import tickers as tickers_set

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAX_TICKERS = 10
# These will be excluded unless there is a $ before them
TICKER_EXCLUSIONS = ["OTM", "ITM", "ATM", "ATH", "MACD", "ROI", "GAIN", "LOSS", "TLDR", "CEO", "WSB", "EOD", "YTD",
                     "LLC", "IMO", "CEO", "CFO", "FBI", "SEC", "THE", "NYSE", "USA", "IMF", "AND", "BABY", "EST", "PDT",
                     "IPO", "YOLO", "LONG", "VEGA", "THETA", "GAMMA", "DELTA", "STOP", "ALL"
                     ]


def parse_tickers_from_text(text) -> [str]:
    punct_chars = """-.%#,'"&/![]()?"""
    # Won't match LULU\ yet
    punct_regex = r"(?:[-.%#,'\"&/!\[\]\(\)\?]*)"
    three_5 = r'{3,5}'
    one_2 = r'{1,2}'
    one_5 = r'{1,5}'
    one = r'{1}'
    match_3_5_maybe_with_dollar = fr'\$?[A-Z]{three_5}(?:\.[A-Z]{one})?{punct_regex}(?=\s|$)'
    match_1_5_lowercase_with_dollar = fr'\$[A-Za-z]{one_5}(?:\.[A-Za-z]{one})?{punct_regex}(?=\s|$)'
    match_1_2_with_dollar = fr'\$[A-Za-z]{one_2}(?:\.[A-Za-z]{one})?{punct_regex}(?=\s|$)'
    ticker_regex = f"{match_3_5_maybe_with_dollar}|{match_1_5_lowercase_with_dollar}|{match_1_2_with_dollar}"

    raw_tickers = [t.upper() for t in re.findall(ticker_regex, text)]

    # Remove matched punctuation on the ends of tickers
    stripped_punct = [t.strip(punct_chars) for t in raw_tickers]

    # Exclude some common terms which we know are not tickers
    for exclusion in TICKER_EXCLUSIONS:
        while exclusion in stripped_punct:
            stripped_punct.remove(exclusion)

    # Add $ to front if it is not there, unique, and sort
    return list(sorted(set(['$' + ticker if ticker[0] != '$' else ticker for ticker in stripped_punct])))


def get_tickers_for_submission(submission: Submission) -> [str]:
    logger.debug(submission.title + "\n" + (submission.selftext if submission.is_self else "LINK POST\n"))
    tickers = parse_tickers_from_text(submission.title + "\n" + ((submission.selftext + "\n") if submission.is_self else "\n"))
    # A post might spam capital words, so if we detect more than 10 tickers, don't return it
    if len(tickers) <= MAX_TICKERS or submission.link_flair_text == 'DD':
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


def reply_to(item: Union[Message, Comment], message: str):
    item.reply(message)


def create_subscription_notification(tickers: [str]):
    return f'You\'ll be notified when DD is posted for {", ".join(tickers)}\n\n\n\n' +\
        'To stop subscriptions reply with a message like `stop $MSFT $AAPL`'


def create_unsubscription_notification(tickers: [str]):
    return f'You are no longer subscribed to {", ".join(tickers)}'


def create_all_subscription_notification():
    # u.message(
    #     "I've subscribed you to all DD",
    #     "You'll be notified when any new DD is posted\n\n\n\n" +
    #     'To stop your subscription to all DD, reply `stop all`'
    # )
    ticker = random.choice(tuple(tickers_set))
    return "The ALL DD feed is temporarily disabled\n\n" +\
        "You'll still be subscribed, but you won't receive notifications until it's re-enabled\n\n\n\n" +\
        f'In the meantime, you can subscribe to DD for specific tickers [here](https://np.reddit.com/message/compose/?to=WSBStockTickerBot&subject=Subscribe%20Me&message=%20%24{ticker})'


def create_all_unsubscription_notification():
    return "I've unsubscribed you from the all DD feed\n\n" +\
        "You'll still receive notifications for individual tickers which you are subscribed to"


def create_error_notification():
    return "I couldn't understand what you sent\n\n" +\
        "Be sure to include at least one real ticker in your message\n\n" +\
        "[Try reading these instructions on how to use me](https://www.reddit.com/user/WSBStockTickerBot/comments/gt375p/how_to_use_me/)"


def make_comment_from_tickers(tickers: [str]):
    ticker = random.choice(tuple(tickers_set))
    ticker2 = random.choice(tuple(tickers_set))
    return (
        "I'm a bot, REEEEEEE\n\n"
        f"I've found these tickers in this submission: {' '.join([create_send_link_for_ticker(t) for t in tickers])}\n\n"
        "I can notify you when DD is posted about these tickers in the future\n\n"
        f'Click on the ticker above to subscribe or click [here]({create_send_link_for_tickers(tickers)}) to be subscribed to all tickers in this post\n\n'
        f"Comment below or send me a private message (not a chat!) like `${ticker} ${ticker2}` to subscribe to other tickers\n\n"
        "Read how to use me [here](https://www.reddit.com/user/WSBStockTickerBot/comments/gt375p/how_to_use_me/)"
    )


def create_send_link_for_ticker(ticker: str) -> str:
    return f'[{ticker}](https://np.reddit.com/message/compose/?to=WSBStockTickerBot&subject=Subscribe%20Me&message={ticker})'


def create_send_link_for_tickers(tickers: [str]) -> str:
    url_encoded_tickers = urllib.parse.quote(' '.join(tickers))
    return f'https://np.reddit.com/message/compose/?to=WSBStockTickerBot&subject=Subscribe%20Me&message={url_encoded_tickers}'


def make_pretty_message(ticker_notifications: [{}]) -> str:
    def make_title_links(submissions: [Submission]):
        title_links = ""
        for s in submissions:
            title_links += f'- [{s.title}]({s.permalink})\n'
        return title_links

    pretty_message = ""
    for n in ticker_notifications:
        pretty_message += f'## {n["ticker"]}:\n{make_title_links(n["subs"])}\n\n'
    return pretty_message


def chunks(data, size):
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}