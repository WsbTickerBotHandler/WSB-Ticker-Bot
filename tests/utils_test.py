from functools import partial

from defaults import TICKER_EXCLUSIONS
from fixtures import *
from submission_utils import SubmissionNotification
from utils import chunks, create_notifications, get_tickers_for_submission, group_submissions_for_tickers, \
    is_account_old_enough, parse_tickers_from_text, should_sleep_for_seconds, encode_notification_for_sqs, decode_notification_from_sqs


def test_chunks():
    data = {'a': [1], 'b': [2, 3, 4], 'c': [5], 'd': [6], 'e': [7]}
    assert list(chunks(data, 2)) == [{'a': [1], 'b': [2, 3, 4]}, {'c': [5], 'd': [6]}, {'e': [7]}]


def test_create_notifications():
    def mock_get_subscribed_users(ticker: str) -> [str]:
        if ticker == "$WISA":
            return ["u1", "u2"]
        else:
            return ["u1", "u3"]

    tickers_with_submissions = {
        "$FNJN": [
            SubmissionNotification('a1', 'DD', 'test.permalink1', 'test-submission1'),
            SubmissionNotification('a2', 'DD', 'test.permalink2', 'test-submission2')
        ],
        "$WISA": [
            SubmissionNotification('a1', 'DD', 'test.permalink1', 'test-submission1'),
        ]
    }
    notifications = create_notifications(tickers_with_submissions, partial(mock_get_subscribed_users))
    expected_result = {
        # User 1 is notified about FNJN which occurs in both posts and also about WISA which only occurs in one of them
        'u1': [{
            'ticker': '$FNJN',
            'subs': [SubmissionNotification(id='a1', link_flair_text='DD', permalink='test.permalink1',
                                            title='test-submission1'),
                     SubmissionNotification(id='a2', link_flair_text='DD', permalink='test.permalink2',
                                            title='test-submission2')]
        },
            {
                'ticker': '$WISA',
                'subs': [SubmissionNotification(id='a1', link_flair_text='DD', permalink='test.permalink1',
                                                title='test-submission1')],
            }],
        # User 2 is notified about WISA which occurs only in one of the posts
        'u2': [{
            'ticker': '$WISA',
            'subs': [SubmissionNotification(id='a1', link_flair_text='DD', permalink='test.permalink1',
                                            title='test-submission1')]
        }],
        # User 3 is notified about FNJN which occurs in both posts
        'u3': [{
            'ticker': '$FNJN',
            'subs': [SubmissionNotification(id='a1', link_flair_text='DD', permalink='test.permalink1',
                                            title='test-submission1'),
                     SubmissionNotification(id='a2', link_flair_text='DD', permalink='test.permalink2',
                                            title='test-submission2')]
        }]
    }
    assert notifications == expected_result


@pytest.mark.integration
def test_get_tickers_for_submission(a_submission: Submission):
    assert get_tickers_for_submission(a_submission) == ['$ATH', '$GAIN', '$SPXL', '$SPY']


@pytest.mark.integration
def test_group_submissions_for_tickers(a_submission: Submission):
    def mock_had_already_processed_id_true(submission_id: str) -> bool: return True

    def mock_had_already_processed_id_false(submission_id: str) -> bool: return False

    expected_result = {
        '$ATH': [
            SubmissionNotification(id='gn18pl', link_flair_text=None, permalink='/r/test/comments/gn18pl/check_it_out/',
                                   title='Check it out')],
        '$GAIN': [
            SubmissionNotification(id='gn18pl', link_flair_text=None, permalink='/r/test/comments/gn18pl/check_it_out/',
                                   title='Check it out')],
        '$SPXL': [
            SubmissionNotification(id='gn18pl', link_flair_text=None, permalink='/r/test/comments/gn18pl/check_it_out/',
                                   title='Check it out')],
        '$SPY': [
            SubmissionNotification(id='gn18pl', link_flair_text=None, permalink='/r/test/comments/gn18pl/check_it_out/',
                                   title='Check it out')]
    }
    assert group_submissions_for_tickers([a_submission], partial(mock_had_already_processed_id_false)) == expected_result
    assert group_submissions_for_tickers([a_submission], partial(mock_had_already_processed_id_true)) == {}


@pytest.mark.integration
def test_is_account_old_enough(a_user: Redditor):
    assert is_account_old_enough(a_user) is True


text = f'''
        $Rip airlines
        VEM is going to moon
        {str(TICKER_EXCLUSIONS)} 
        $ATH $GAIN should be included
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
    expected_out = ['$AAAU', '$AADR', '$ATH', '$MGM', '$CZR', '$BF.A', '$BIOX.W', '$BRK.A', '$BRK.B', '$BRMK.W', '$DIS', '$GAIN', '$LULU', '$R', '$SPXL',
                    '$SPY', '$VTIQ', '$Z']
    assert parse_tickers_from_text(text) == sorted(expected_out)


def test_sleep_for_time():
    text_second = 'try again in 1 second'
    text_seconds = 'try again in 2 seconds'
    text_minutes = 'try again in 1 minutes'
    should_sleep_for_seconds(text_second)
    should_sleep_for_seconds(text_seconds)
    # sleep_for_time(text_minutes)


def test_encode_decode():
    notification = {'SomeUser': [{
        'subs': [SubmissionNotification(
            id='gn18pl',
            link_flair_text=None,
            permalink='/r/test/comments/gn18pl/check_it_out/',
            title='Check it out'
        )],
        'ticker': '$SPY'
    }]}

    string = encode_notification_for_sqs(notification)
    result = decode_notification_from_sqs(string)
    assert result['SomeUser'][0]['ticker'] == "$SPY"
