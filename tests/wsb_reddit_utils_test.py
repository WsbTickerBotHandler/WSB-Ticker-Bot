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
        $MGM/$CZR/etc is ok
        AAAU: this should be here
        AADR; this should also
        "$SPXL" with quotes should be detected
        South Park has known how the fed operates since 2009
        SPY Perhaps my friend isn’t ready for trading after all...
        Warren Buffet
    '''


def test_parse_tickers_from_text():
    expected_out = [
        '$AAAU', '$AADR', '$MGM', '$CZR',
        '$ASMR', '$ATH', '$BBWT', '$BF.A', '$BIOX.W', '$BRK.A', '$BRK.B', '$BRMK.W', '$DIS', '$FBI', '$FIVES', '$GAIN',
        '$LULU', '$R', '$RIP', '$SPX', '$SPXL', '$SPY', '$VEM', '$VTIQ', '$Z', '$ZZ'
    ]
    assert parse_tickers_from_text(text) == sorted(expected_out)


def test_make_comment_from_tickers(a_user: Redditor):
    msg = make_comment_from_tickers(["$SPY", "$TSLA", "$AAPL"])
    a_user.message("test_make_comment_from_tickers", msg)


@pytest.mark.integration
def test_account_is_older_than(a_user: Redditor):
    assert is_account_old_enough(a_user) is True
