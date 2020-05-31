import os
import pickle

combined_file_name = f'{os.path.dirname(__file__)}/combined.pkl'


def load_tickers():
    with open(combined_file_name, 'rb') as f:
        return pickle.load(f)


tickers = load_tickers()
