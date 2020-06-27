BOT_USERNAME = "WSBStockTickerBot"
BOT_HELPER_USERNAME = "WSBTickerBotHandler"
DEFAULT_ACCOUNT_AGE = 15
DEFAULT_SUBMISSION_RETRIEVE_LIMIT = 30
DEFAULT_REPROCESS = False
MAX_NOTIFICATION_THREADPOOL_WORKERS = 6
MAX_TICKERS_ALLOWED_IN_SUBMISSION = 30
MAX_TICKERS_TO_SUBSCRIBE_AT_ONCE = 10
MAX_USERS_TO_NOTIFY_PER_CHUNK = 60
SUBREDDIT = 'wallstreetbets'
# These will be excluded unless there is a $ before them
TICKER_EXCLUSIONS = ["OTM", "ITM", "ATM", "ATH", "MACD", "ROI", "GAIN", "LOSS", "TLDR", "CEO", "WSB", "EOD", "YTD",
                     "LLC", "IMO", "CEO", "CFO", "FBI", "SEC", "THE", "NYSE", "USA", "IMF", "AND", "BABY", "EST", "PDT",
                     "IPO", "YOLO", "LONG", "VEGA", "THETA", "GAMMA", "DELTA", "STOP", "ALL"
                     ]
UNREAD_MESSAGES_TO_PROCESS = 50
# VALID_FLAIRS = {'DD', 'Discussion', 'Fundamentals'}
VALID_FLAIRS = {'DD'}
