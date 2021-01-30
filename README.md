I'll set the scene for you. It's 1:03pm on a Friday. You've just worked hard to finish page 8 of the coloring book your wife's boyfriend bought you for Christmas last year. You deserve a break. Before nap time, you open RH only to see a 4x gilded post circle-jerking over the 10-bagger earnings play they've been milking over the last week. You stare, blank faced at the post. Your brain faintly remembers the ticker from months ago when your friend told you the company would blow up during the beer virus. The rage builds even as the half-eaten crayon hanging out of the side of your mouth wets with drool. A single syllable _guhhhh_ releases from your mouth as you realize the tendies could have been yours if only your feeble brain had processed enough TLDRs to fool you into buying a call


# If this sounds like you, I've built something to help you out next time you need someone to hold your hand while you confidently swipe up on some OTM weeklies

**[/u/WSBStockTickerBot](https://www.reddit.com/user/WSBStockTickerBot) scans [/r/wsb](https://www.reddit.com/r/wallstreetbets/ "WSB")'s new posts and will notify you when DD is being posted about tickers you're interested in**

## How to use
~~**EASY>>** [CLICK HERE TO SUBSCRIBE TO A TICKER(S)!](https://np.reddit.com/message/compose/?to=WSBStockTickerBot&subject=Subscribe%20Me&message=Type%20tickers%20%24LIKE%20%24THIS%20anywhere%20in%20this%20message%20to%20subscribe%20to%20them) **<<EASY**~~
Looks like there's too many of us and the bot is getting rate limited. While I search for a workaround (if one exists), please subscribe to tickers individually below

**EASY>>** [CLICK HERE TO SUBSCRIBE TO ALL NEW DD!](https://np.reddit.com/message/compose/?to=WSBStockTickerBot&subject=Subscribe%20Me&message=ALL%20DD) **<<EASY**

Or...

* Send [/u/WSBStockTickerBot](https://www.reddit.com/user/WSBStockTickerBot) a message or comment on something it's posted. **Chat is not supported by Reddit for bots please make sure you send a DM or respond to a [/u/WSBStockTickerBot](https://www.reddit.com/user/WSBStockTickerBot) comment**
  * Example: `$ESGV $UCO $GE` will subscribe you to the `$ESGV`, `$UCO` and `$GE` tickers
* Use a message with stop at the beginning to be unsubscribed from specific tickers
  * Example: `STOP $UCO $GE`
~~* Use `STOP ALL` to unsubscribe from the "ALL DD" feed~~ DISABLED, see above

## A couple things to know
* If you subscribed to an individual ticker you'll be notified of new posts with the `DD` flair for that ticker
~~* If you subscribed to the "ALL DD" feed, you'll be notified of all new `DD` flaired posts~~
* Stopping your "ALL DD" subscription will not stop individual tickers you've subscribed to separately

* If you find any issues or have a suggestion or feature you'd like to see, send a message to [/u/WSBTickerBotHandler](https://www.reddit.com/user/WSBTickerBotHandler) or open an issue/PR here https://github.com/WsbTickerBotHandler/WSB-Ticker-Bot

---

If this bot helped your tendies print consider leaving a tip and I swear to piss it away on FDs or use it to operate the bot

`BTC: 3EspqEdX1jJtR3wifgqkZzUP7Q3AM4aYbk`

`BCH: qzazpxhgyx8xperazwnt8js2pufckyrv2ya49s9vmf`

If you lost money because you read some shit DD then open up the door to the back porch, head outside, smoke some weed and chill the fuck out. Money isn't everything. Except when you yolo your parent's 100k retirement fund. But hey, maybe if you'd seen the right DD that wouldn't have happened

## Development
Setting up the environment
* Create a `praw.ini` file in the root directory of this project with the Reddit bot's account information
```
[WSBStockTickerBot]
client_id=<client-id>
client_secret=<client-secret>
user_agent="lambda:WSBStockTickerBot:v1.0 (by /u/wsbtickerbothandler@gmail.com)"
username=WSBStockTickerBot
password=<password>
```
* Create an `aws-credentials.ini` file in the root directory with your AWS account's information in a profile called `wsb-ticker-bot`
* There's probably a combination of AWS access policies you can use to ensure the bot can only do what it is intended to do but I gave it admin access for now
```
[wsb-ticker-bot]
region = us-west-1
aws_access_key_id=<access-key-id>
aws_secret_access_key=<secret-acccess-key>
```
* Run the credentials configuration script `make configure_credentials`
* General information
    * All commands should be run through the `makefile` and executed at the top-level directory
    * The bot is deployed on lambda and runs every 5 minutes. To deploy, you first have to have an S3 bucket to store the bot's libs. Run `make create_bucket` followed by `make deploy` to do it all
    * A DynamoDB is configured (not set up automatically here) with some tables to track things like whether a particular submission has already been processed by the bot and which users are subscribed to which tickers. You'll fine function in `database.py` accessed throughout the app for these purposes
    * The `utils` folder contains tools for updating the `stock_data` package with an updated list of all valid tickers
    * The top-level function is located in `lambda.py`
    * Top-level operational functions such as `process_inbox` are not tested. All non-externally dependent functions should be unit tested. Most externally dependent functions should be integration tested (tagged with `@pytest.mark.integration` and use a fixture to perform a test with real data)
    
