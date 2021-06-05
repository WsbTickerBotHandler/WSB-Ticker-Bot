configure_credentials:
	cp aws-credentials.ini tests/aws-credentials.ini
	cp praw.ini src/praw.ini
	cp praw.ini tests/praw.ini
update_tickers:
	echo "Pulling tickers from Nasdaq db, pickling them for use in the bot, and storing in src/stock_data/combined.pkl"
	pipenv install --dev
	(cd utils && pipenv run python tickers.py)
	mv utils/combined.pkl src/stock_data/combined.pkl
	rm utils/*.txt
test:
	PYTHONPATH=src AWS_SHARED_CREDENTIALS_FILE=aws-credentials.ini pipenv run py.test tests -m "not integration"
integration_test:
	PYTHONPATH=src AWS_SHARED_CREDENTIALS_FILE=aws-credentials.ini pipenv run py.test tests -m integration
create_bucket:
	AWS_PROFILE=wsb-ticker-bot AWS_CONFIG_FILE=aws-credentials.ini sh make_bucket.sh
deploy:
	AWS_PROFILE=wsb-ticker-bot AWS_CONFIG_FILE=aws-credentials.ini sh deploy.sh
