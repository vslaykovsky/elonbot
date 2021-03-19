import argparse
import json
import os
import re
import sys
import time
from decimal import Decimal
from typing import Dict, Optional

import requests
from unidecode import unidecode

from binance_client import Binance, MarginType
from twitter_utils import create_headers, reset_twitter_subscription_rules
from utils import log


class ElonBot:
    def __init__(self, user: str,
                 crypto_rules: Dict[str, str],
                 asset: str,
                 auto_buy_delay: float,
                 auto_sell_delay: float,
                 use_image_signal: bool,
                 margin_type: MarginType,
                 order_size: float,
                 process_tweet_text: Optional[str],
                 dry_run: bool):
        self.dry_run = dry_run
        self.user = user
        self.crypto_rules = crypto_rules
        self.asset = asset
        self.auto_buy_delay = auto_buy_delay
        self.auto_sell_delay = auto_sell_delay
        self.use_image_signal = use_image_signal
        self.margin_type = margin_type
        self.order_size = order_size
        self.process_tweet_text = process_tweet_text
        if not self.validate_env():
            return
        self.client = Binance(margin_type, key=os.environ['BINANCE_KEY'], secret=os.environ['BINANCE_SECRET'],
                              dry_run=dry_run)
        log('Starting elon.py')
        log('  User:', user)
        log('  Crypto rules:', crypto_rules)
        log('  self.asset:', self.asset)
        log('  Auto buy time:', auto_buy_delay)
        log('  Auto sell time:', auto_sell_delay)
        log('  Use image signal:', use_image_signal)
        log('  Margin type:', margin_type)
        log('  Order size:', order_size)

    @staticmethod
    def get_image_text(uri: str) -> str:
        """Detects text in the file located in Google Cloud Storage or on the Web.
        """
        if uri is None or uri == '':
            return ''
        from google.cloud import vision
        try:
            client = vision.ImageAnnotatorClient()
            image = vision.Image()
            image.source.image_uri = uri
            response = client.text_detection(image=image)
            if response.error.message:
                log('{}\nFor more info on error messages, check: '
                    'https://cloud.google.com/apis/design/errors'.format(response.error.message))
                return ''
            texts = response.text_annotations
            result = ' '.join([text.description for text in texts])
            log('Extracted from the image:', result)
            return result
        except Exception as ex:
            log('Failed to process attached image', ex)
            return ''

    def validate_env(self, verbose=False) -> bool:
        binance_test = ('BINANCE_KEY' in os.environ) and ('BINANCE_SECRET' in os.environ)
        if not binance_test and verbose:
            log('Please, provide BINANCE_KEY and BINANCE_SECRET environment variables')
        google_test = not self.use_image_signal or ('GOOGLE_APPLICATION_CREDENTIALS' in os.environ)
        if not google_test and verbose:
            log('Please, provide GOOGLE_APPLICATION_CREDENTIALS environment variable')
        twitter_test = 'TWITTER_BEARER_TOKEN' in os.environ
        if not twitter_test and verbose:
            log('Please, provide TWITTER_BEARER_TOKEN environment variable')
        return binance_test and google_test and twitter_test

    def buy(self, ticker: str):
        ask_price = self.client.get_ask_price(ticker, self.asset)
        available_cash, _ = self.client.get_available_asset(self.asset, ticker)
        if available_cash == 0:
            log(f'Failed to buy {ticker}, no {self.asset} available')
            return None
        borrowable_cash = self.client.get_max_borrowable(self.asset, ticker)
        if self.order_size == 'max':
            total_cash = available_cash + borrowable_cash
        else:
            max_cash = (available_cash + borrowable_cash) / available_cash
            if float(self.order_size) > max_cash:
                raise ValueError(f"Order size exceeds max margin: {self.order_size} > {max_cash}")
            total_cash = available_cash * Decimal(self.order_size)
        ticker_amount = total_cash / ask_price
        return self.client.buy(ticker_amount, ticker, self.asset)

    def sell(self, ticker: str):
        _, available_ticker = self.client.get_available_asset(self.asset, ticker)
        return self.client.sell(available_ticker, ticker, self.asset)

    def trade(self, ticker: str):
        time.sleep(self.auto_buy_delay)
        buy_result = self.buy(ticker)
        if buy_result is None:
            return None
        log('Waiting for before sell', self.auto_sell_delay)
        time.sleep(self.auto_sell_delay)
        sell_result = self.sell(ticker)
        return buy_result, sell_result

    def process_tweet(self, tweet_json: str):
        tweet_json = json.loads(tweet_json)
        log("Tweet received\n", json.dumps(tweet_json, indent=4, sort_keys=True), "\n")
        tweet_text = tweet_json['data']['text']
        image_url = (tweet_json.get('includes', {}).get('media', [])[0:1] or [{}])[0].get('url', '')
        image_text = ''
        if self.use_image_signal:
            image_text = ElonBot.get_image_text(image_url)
        full_text = f'{tweet_text} {image_text}'
        for re_pattern, ticker in self.crypto_rules.items():
            t = unidecode(full_text)
            if re.search(re_pattern, t, flags=re.I) is not None:
                log(f'Tweet matched pattern "{re_pattern}", buying corresponding ticker {ticker}')
                return self.trade(ticker)
        return None

    def run(self, timeout: int = 24 * 3600) -> None:
        if self.process_tweet_text is not None:
            self.process_tweet(self.process_tweet_text)
            return
        reset_twitter_subscription_rules(self.user)
        while True:
            try:
                params = {'expansions': 'attachments.media_keys',
                          'media.fields': 'preview_image_url,media_key,url',
                          'tweet.fields': 'attachments,entities'}
                response = requests.get(
                    "https://api.twitter.com/2/tweets/search/stream",
                    headers=create_headers(), params=params, stream=True, timeout=timeout
                )
                log('Subscribing to twitter updates. HTTP status:', response.status_code)
                if response.status_code != 200:
                    raise Exception("Cannot get stream (HTTP {}): {}".format(response.status_code, response.text))
                for response_line in response.iter_lines():
                    if response_line:
                        self.process_tweet(response_line)
            except Exception as ex:
                log(ex, 'restarting socket')
                time.sleep(60)
                continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Trade cryptocurrency at Binance using Twitter signal')
    parser.add_argument('--user', help='Twitter user to follow. Example: elonmusk', required=True)
    parser.add_argument('--crypto-rules', help='JSON dictionary, where keys are regexp patterns, '
                                               'values are corresponding cryptocurrency tickers', required=True,
                        default=json.dumps({'doge': 'DOGE', 'btc|bitcoin': 'BTC'}))
    parser.add_argument('--margin-type', type=MarginType, choices=list(MarginType), required=True)
    parser.add_argument('--auto-buy-delay', type=float, help='Buy after auto-buy-delay seconds', default=10)
    parser.add_argument('--auto-sell-delay', type=float, help='Sell after auto-sell-delay seconds', default=60 * 5)
    parser.add_argument('--asset', default='USDT', help='asset to use to buy cryptocurrency')
    parser.add_argument('--use-image-signal', action='store_true',
                        help='Extract text from attached twitter images using Google OCR',
                        default=True)
    parser.add_argument('--order-size', help='Size of orders to execute. 1.0 means 100% of the deposit; '
                                             '0.5 - 50% of the deposit; 2.0 - 200% of the deposit (marginal trade)'
                                             '"max" - maximum borrowable amount', default='max')
    parser.add_argument('--dry-run', action='store_true', help="Don't execute orders", default=False)
    parser.add_argument('--process-tweet',
                        help="Don't subscribe to Twitter feed, only process a single tweet (useful for testing)",
                        default=None)
    args = parser.parse_args()
    bot = ElonBot(args.user,
                  json.loads(args.crypto_rules),
                  args.asset,
                  args.auto_buy_delay,
                  args.auto_sell_delay,
                  args.use_image_signal,
                  args.margin_type,
                  args.order_size,
                  args.process_tweet,
                  args.dry_run)
    if not bot.validate_env(verbose=True):
        sys.exit(-1)
    bot.run()
