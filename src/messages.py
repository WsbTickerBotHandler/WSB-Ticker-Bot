import logging
import random
import urllib.parse
from typing import Union

from praw.models import Message, Comment, Submission

from defaults import DEFAULT_ACCOUNT_AGE
from stock_data.tickers import tickers as tickers_set

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def reply_to(item: Union[Message, Comment], message: str):
    try:
        item.reply(message)
    except Exception as e:
        logger.error(f"There was an error responding to user {item.author}'s message with id {item.id}: {e} ")


def create_subscription_notification(tickers: [str]):
    tickers_for_stop_example = random.choices(tickers, k=2) if len(tickers) > 1 else tickers[:1]
    return f'You\'ll be notified when DD is posted for {", ".join(tickers)}\n\n\n\n' + \
           f'To stop subscriptions reply with a message like `stop {" ".join(tickers_for_stop_example)}`'


def create_unsubscription_notification(tickers: [str]):
    return f'You are no longer subscribed to {", ".join(tickers)}'


def create_all_subscription_notification():
    # u.message(
    #     "I've subscribed you to all DD",
    #     "You'll be notified when any new DD is posted\n\n\n\n" +
    #     'To stop your subscription to all DD, reply `stop all`'
    # )
    return "The ALL DD feed is temporarily disabled\n\n" + \
           "You'll still be subscribed, but you won't receive notifications until it's re-enabled\n\n\n\n" + \
           f'In the meantime, you can subscribe to DD for specific tickers [here](https://np.reddit.com/message/compose/?to=WSBStockTickerBot&subject=Subscribe%20Me&message=Type%20tickers%20%24LIKE%20%24THIS%20anywhere%20in%20this%20message%20to%20subscribe%20to%20them)'


def create_all_unsubscription_notification():
    return "I've unsubscribed you from the all DD feed\n\n" + \
           "You'll still receive notifications for individual tickers which you are subscribed to"


def create_error_notification():
    return "I couldn't understand what you sent\n\n" + \
           "Be sure to include at least one real ticker in your message\n\n" + \
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


def create_user_not_old_enough() -> str:
    return f'Your account must be older than {DEFAULT_ACCOUNT_AGE} days to use the bot'


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
