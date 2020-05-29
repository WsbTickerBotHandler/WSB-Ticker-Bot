#!/bin/bash
BUCKET_ID=$(dd if=/dev/random bs=4 count=1 2>/dev/null | od -An -tx1 | tr -d ' \t\n')
BUCKET_NAME=wsb-ticker-bot-lambda-artifacts-$BUCKET_ID
echo $BUCKET_NAME > bucket-name.txt
aws s3 mb s3://$BUCKET_NAME