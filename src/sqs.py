import os

import boto3
from boto3 import Session
from botocore.exceptions import ProfileNotFound

from utils import chunk_list, encode_notification_for_sqs


class SQS:
    def __init__(self, queue_url=None):
        try:
            # Useful for local development using an aws profile, will fail on lambda but method below will succeed
            self.session: Session = boto3.session.Session(profile_name="wsb-ticker-bot")
        except ProfileNotFound:
            self.session: Session = boto3.session.Session()
        self.client = self.session.client('sqs')

        if queue_url is not None:
            self.queue_url = queue_url
        else:
            self.queue_url = os.environ["NotificationsQueueUrl"]

    def send_notification(self, notification):
        self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=encode_notification_for_sqs(notification)
        )

    def send_notification_batch(self, notifications):
        total = []
        for entries_chunk in chunk_list(notifications, 10):
            total.append(encode_notification_for_sqs(entries_chunk))

        for chunk_of_total in chunk_list(total, 10):
            self.client.send_message_batch(
                QueueUrl=self.queue_url,
                Entries=[self.create_notification_message(e) for e in chunk_of_total]
            )

    def delete_notification(self, notification_receipt_handle):
        self.client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=notification_receipt_handle
        )

    @staticmethod
    def create_notification_message(notification):
        return {
            'Id': str(hash(str(notification))),
            'MessageBody': notification
        }
