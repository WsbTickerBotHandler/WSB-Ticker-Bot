#!/bin/bash
pipenv run pip freeze > requirements.txt
mkdir -p package/python
pip install --target package/python -r requirements.txt --upgrade && \
ARTIFACT_BUCKET=$(cat bucket-name.txt) && \
aws cloudformation package --template-file template.yml --s3-bucket "$ARTIFACT_BUCKET" --output-template-file out.yml && \
aws cloudformation deploy --template-file out.yml --stack-name wsb-ticker-bot --capabilities CAPABILITY_NAMED_IAM
