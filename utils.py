from datetime import datetime


def log(*params):
    print(datetime.now(), flush=True, *params)
