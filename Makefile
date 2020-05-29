test:
	PYTHONPATH=src AWS_SHARED_CREDENTIALS_FILE=aws-credentials.ini py.test tests -m "not integration"
integration_test:
	PYTHONPATH=src AWS_SHARED_CREDENTIALS_FILE=aws-credentials.ini py.test tests -m integration

create_bucket:
	sh make_bucket.sh

package_lambda:
	sh package_lambda.sh
