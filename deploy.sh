#!/bin/bash
pipenv lock -r > requirements.txt
mkdir -p package/python
pip3 install --target deployment/package/python -r requirements.txt --upgrade && \
ARTIFACT_BUCKET=$(cat bucket-name.txt) && \
aws cloudformation package \
  --template-file deployment/template.yml \
  --s3-bucket "$ARTIFACT_BUCKET" \
  --output-template-file deployment/out.yml && \
aws cloudformation deploy \
  --template-file deployment/out.yml \
  --stack-name wsb-ticker-bot \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides Version="$(git rev-parse --short HEAD)"
