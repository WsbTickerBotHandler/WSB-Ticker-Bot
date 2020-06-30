import os
import pickle

import boto3
from boto3 import Session
from botocore.exceptions import ProfileNotFound


class Kinesis:
    def __init__(self, stream_name=None):
        try:
            # Useful for local development using an aws profile, will fail on lambda but method below will succeed
            self.session: Session = boto3.session.Session(profile_name="wsb-ticker-bot")
        except ProfileNotFound:
            self.session: Session = boto3.session.Session()
        self.client = self.session.client('kinesis')

        if stream_name is not None:
            self.stream_name = stream_name
        else:
            self.stream_name = os.environ["NotificationsStreamName"]

    def send_notification_batch(self, notifications):
        self.client.put_records(
            StreamName=self.stream_name,
            Records=[self.create_notification_message(n) for n in notifications]
        )

    @staticmethod
    def create_notification_message(notification):
        return {
            'Data': pickle.dumps(notification),
            'PartitionKey': 'default'
        }
