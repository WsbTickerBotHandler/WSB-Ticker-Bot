import boto3
from datetime import timedelta, datetime
from boto3 import Session
from botocore.exceptions import ProfileNotFound

COMMENTED_SUBMISSIONS_TABLE_NAME = 'commented-submissions'
NOTIFIED_SUBMISSIONS_TABLE_NAME = 'notified-submissions'
SENT_NOTIFICATIONS_TABLE_NAME = 'sent-notifications'
# Users who have blocked the bot, do not attemp to send
BLOCKED_USERS_TABLE_NAME = 'blocked-users'


class Database:
    def __init__(self):
        try:
            # Useful for local development using an aws profile, will fail on lambda but method below will succeed
            self.session: Session = boto3.session.Session(profile_name="wsb-ticker-bot")
        except ProfileNotFound:
            self.session: Session = boto3.session.Session()
        self.client = self.session.client('dynamodb')

    def get_users_subscribed_to_ticker(self, ticker: str) -> [str]:
        try:
            return self.client.get_item(
                TableName='dd-notifications',
                Key={
                    'ticker': {'S': ticker}
                },
                ProjectionExpression='subscribed_users'
            )['Item']['subscribed_users']['SS']
        except KeyError:
            return []

    def subscribe_user_to_ticker(self, user: str, ticker: str) -> [str]:
        return self.client.update_item(
            TableName='dd-notifications',
            Key={
                'ticker': {'S': ticker}
            },
            UpdateExpression='ADD subscribed_users :userToSubscribe',
            ExpressionAttributeValues={
                ':userToSubscribe': {'SS': [user]}
            },
            ReturnValues='UPDATED_NEW'
        )['Attributes']['subscribed_users']['SS']

    def unsubscribe_user_from_ticker(self, user: str, ticker: str) -> [str]:
        try:
            return self.client.update_item(
                TableName='dd-notifications',
                Key={
                    'ticker': {'S': ticker}
                },
                UpdateExpression='DELETE subscribed_users :userToUnsubscribe',
                ExpressionAttributeValues={
                    ':userToUnsubscribe': {'SS': [user]}
                },
                ReturnValues='UPDATED_NEW'
            )['Attributes']['subscribed_users']['SS']
        except KeyError:
            return []

    def has_already_processed(self, submission_id, table_name) -> bool:
        try:
            self.client.get_item(
                TableName=table_name,
                Key={
                    'submission_id': {'S': submission_id}
                }
            )['Item']
            return True
        except KeyError:
            return False

    def user_has_blocked_bot(self, user_id, table_name) -> bool:
        try:
            self.client.get_item(
                TableName=table_name,
                Key={
                    'user_id': {'S': user_id}
                }
            )['Item']
            return True
        except KeyError:
            return False

    def has_already_notified(self, notification_id: str) -> bool:
        try:
            self.client.get_item(
                TableName=SENT_NOTIFICATIONS_TABLE_NAME,
                Key={
                    'id': {'S': notification_id}
                }
            )['Item']
            return True
        except KeyError:
            return False

    def add_submission_marker(self, table_name, submission_id):
        return self.client.put_item(
            TableName=table_name,
            Item={
                'submission_id': {'S': submission_id}
            },
            ReturnValues='NONE'
        )

    def add_notification_marker(self, notification_id):
        ttl = (datetime.now() + timedelta(days=5)).timestamp()
        return self.client.put_item(
            TableName=SENT_NOTIFICATIONS_TABLE_NAME,
            Item={
                'id': {'S': notification_id},
                'ttl': {'N': str(int(ttl))}
            },
            ReturnValues='NONE'
        )

    def add_blocked_user(self, user_id):
        return self.client.put_item(
            TableName=BLOCKED_USERS_TABLE_NAME,
            Item={
                'user_id': {'S': user_id}
            },
            ReturnValues='NONE'
        )

    def subscribe_user_to_all_dd_feed(self, user_name: str):
        self.client.put_item(
            TableName='all-dd-subscribers',
            Item={
                'user_name': {'S': user_name}
            },
            ReturnValues='NONE'
        )

    def unsubscribe_user_from_all_dd_feed(self, user_name: str):
        self.client.delete_item(
            TableName='all-dd-subscribers',
            Key={
                'user_name': {'S': user_name}
            },
            ReturnValues='NONE'
        )

    def is_user_subscribed_to_all_dd_feed(self, user_name: str):
        try:
            self.client.get_item(
                TableName='all-dd-subscribers',
                Key={
                    'user_name': {'S': user_name}
                }
            )['Item']
            return True
        except KeyError:
            return False

    def get_users_subscribed_to_all_dd_feed(self) -> [str]:
        try:
            return [i['user_name']['S'] for i in self.client.scan(TableName='all-dd-subscribers')['Items']]
        except KeyError:
            return []
