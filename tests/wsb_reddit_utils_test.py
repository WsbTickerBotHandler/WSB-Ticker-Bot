import pytest

from wsb_reddit_utils import *
from fixtures import *


text = f'''
        $Rip airlines
        VEM is going to moon
        {str(TICKER_EXCLUSIONS)} 
        $ATH $FBI $GAIN should be included if a dollar sign exists before them
        FIVES five letter tickers
        $FIVES five letter tickers with dollar sign
        $R should be matched but T shouldn't be
        $BRK.A and $BRMK.W should be matched
        BRK.B and BIOX.W should be matched
        $BF.A should be matched
        TLDR: should be excluded
        ($LULU.) should be included
        VTIQ... should be too
        Invest in What's Real: SPY
        OTM and ITM should not be matched nor at the end OTM
        $DIS yolo on earnings and DD
        Welcome to Fabulous Wallstreetbets
        ASMR will crash
        BBWT will also moon
        $Z sucks, more like $ZZ
        Papa Buffet $ASMR
        SPX
        South Park has known how the fed operates since 2009
        SPY Perhaps my friend isn’t ready for trading after all...
        Warren Buffet
    '''


def test_parse_tickers_from_text():
    expected_out = [
        '$ASMR', '$ATH', '$BBWT', '$BF.A', '$BIOX.W', '$BRK.A', '$BRK.B', '$BRMK.W', '$DIS', '$FBI', '$FIVES', '$GAIN',
        '$LULU', '$R', '$RIP', '$SPX', '$SPY', '$VEM', '$VTIQ', '$Z', '$ZZ'
    ]
    assert parse_tickers_from_text(text) == expected_out


def test_make_comment_from_tickers():
    expected_coment = (
        "I'm a bot, REEEEEEEEEEE\n\n"
        "I've identified these tickers in this submission: $SPY, $TSLA, $AAPL\n\n"
        "To be notified of future DD posts that include a particular ticker comment "
        "with the ticker names and I'll message you when a DD post about that ticker is rising.\n\n"
        "Example: $TSLA $AAPL"
    )
    assert make_comment_from_tickers(["$SPY", "$TSLA", "$AAPL"]) == expected_coment


@pytest.mark.integration
def test_notify_user_of_error(a_submission, a_user: Redditor):
    notify_user_of_error(a_user)
