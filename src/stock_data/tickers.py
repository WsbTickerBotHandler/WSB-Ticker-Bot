import os

combined_file_name = f'{os.path.dirname(__file__)}/combined.txt'


def load_tickers():
    s = set()
    with open(combined_file_name) as f:
        for line in f:
            s.add(line.strip('\n'))
    return s


tickers = load_tickers()
