#!/bin/bash
BUCKET_ID=$(date +%s)
BUCKET_NAME=wsb-ticker-bot-lambda-artifacts-$BUCKET_ID
echo $BUCKET_NAME > bucket-name.txt
aws s3 mb s3://$BUCKET_NAME
# Use this to delete objects older than a set number of days
#aws s3api put-public-access-block \
#    --bucket "$BUCKET_NAME" \
#    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
aws s3api put-bucket-lifecycle-configuration \
    --bucket "$BUCKET_NAME" \
    --lifecycle-configuration file://deployment/bucket-lifecycle-configuration.json
