import pytest

from database import *


@pytest.fixture(scope="module")
def db_client():
    yield Database()


@pytest.mark.integration
def test_get_users_subscribed_to_ticker(db_client):
    assert db_client.get_users_subscribed_to_ticker("$JUJU") == ["User0", "User1", "User2"]
    assert db_client.get_users_subscribed_to_ticker("$NONE") == []


@pytest.mark.integration
def test_subscribe_user_to_ticker(db_client):
    assert db_client.subscribe_user_to_ticker("User0", "$JUJU") == ["User0", "User1", "User2"]


@pytest.mark.integration
def test_unsubscribe_user_from_ticker(db_client):
    assert db_client.unsubscribe_user_from_ticker("User2", "$JUJU") == ["User0", "User1"]


@pytest.mark.integration
def test_has_already_commented(db_client):
    assert db_client.has_already_processed("asdf") == True
    assert db_client.has_already_processed("not_commented") == False


@pytest.mark.integration
def test_add_submission_marker(db_client):
    db_client.add_submission_marker(NOTIFIED_SUBMISSIONS_TABLE_NAME, "asdf")
