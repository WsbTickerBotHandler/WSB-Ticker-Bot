import boto3
from boto3 import Session

COMMENTED_SUBMISSIONS_TABLE_NAME = 'commented-submissions'
NOTIFIED_SUBMISSIONS_TABLE_NAME = 'notified-submissions'


class Database:
    def __init__(self):
        # Useful for local development using an aws profile
        # self.session: Session = boto3.session.Session(profile_name="wsb-ticker-bot")
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

    def has_already_processed(self, table_name, submission_id) -> bool:
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

    def add_submission_marker(self, table_name, submission_id):
        return self.client.put_item(
            TableName=table_name,
            Item={
                'submission_id': {'S': submission_id}
            },
            ReturnValues='NONE'
        )

    def ticker_exists(self, symbol: str) -> bool:
        try:
            self.client.get_item(
                TableName='stock-symbols',
                Key={
                    'symbol': {'S': symbol.strip("$")}
                }
            )['Item']
            return True
        except KeyError:
            return False
