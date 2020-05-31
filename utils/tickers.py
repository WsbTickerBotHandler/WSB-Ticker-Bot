import os
import wget
import time
from database import Database

nasdaq_tickers_file_name = 'nasdaqlisted.txt'
other_tickers_file_name = 'otherlisted.txt'
combined_file_name = f'{os.path.dirname(__file__)}/combined.txt'

main_tickers_ftp = 'ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt'
other_tickers_ftp = 'ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt'


def download_tickers():
    wget.download(main_tickers_ftp)
    wget.download(other_tickers_ftp)


def process_tickers():
    import csv
    csv.register_dialect('piper', delimiter='|', quoting=csv.QUOTE_NONE)
    all_tickers = []
    with open(nasdaq_tickers_file_name) as nasdaq_tickers_file, open(other_tickers_file_name) as other_tickers_file:
        for row in csv.DictReader(nasdaq_tickers_file, dialect='piper'):
            all_tickers.append(row['Symbol'])
        # Remove meta info
        all_tickers = all_tickers[:-1]
        for row in csv.DictReader(other_tickers_file, dialect='piper'):
            all_tickers.append(row['ACT Symbol'])
        all_tickers = all_tickers[:-1]
        with open(combined_file_name, 'w+') as f:
            f.write("\n".join(all_tickers))

        # Uncomment to write to DB, otherwise just update the file and it is small enough to be committed and used
        # chunked_symbols = divide_chunks(all_tickers, 25)
        #
        # client = Database().client
        #
        # for chunk in chunked_symbols:
        #     client.batch_write_item(
        #         RequestItems={
        #             'stock-symbols': [create_batch_request_items(s) for s in chunk]
        #         }
        #     )
        #     time.sleep(1.01)
        #
        # # Updated every ~6 hours
        # table = client.describe_table(
        #     TableName='stock-symbols'
        # )
        # print(table)


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def create_batch_request_items(symbol: str):
    return {
        'PutRequest': {
            'Item': {
                'symbol': {
                    'S': symbol
                }
            }
        }
    }


if __name__ == '__main__':
    # download_tickers()
    process_tickers()
