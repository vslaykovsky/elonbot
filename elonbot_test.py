import os
import unittest
from unittest.mock import patch

import binance.client

import elonbot
from binance_client import MarginType
from elonbot import ElonBot


class ElonBotTest(unittest.TestCase):

    def setUp(self) -> None:
        os.environ['BINANCE_KEY'] = 'binance key'
        os.environ['BINANCE_SECRET'] = 'binance secret'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google app credentials'
        os.environ['TWITTER_BEARER_TOKEN'] = 'TWITTER_BEARER_TOKEN'

    @patch.object(binance.client.Client, 'get_margin_account',
                  lambda _: {'userAssets': [{'asset': 'USDT', 'free': 12345}, {'asset': 'DOGE', 'free': 12345}]})
    @patch.object(binance.client.Client, 'get_orderbook_ticker', lambda _, symbol: {'askPrice': 0.05})
    @patch.object(binance.client.Client, 'get_max_margin_loan', lambda _, asset: {'amount': 12345})
    @patch.object(binance.client.Client, 'create_margin_order', lambda _, **params: 'order_id')
    @patch.object(elonbot.ElonBot, 'get_image_text', lambda url: '')
    def test_trigger(self):
        bot = ElonBot('elonmusk', {'doge': 'DOGE', 'btc|bitcoin': 'BTC'}, 'USDT', 1, 2, True,
                      MarginType.CROSS_MARGIN,
                      2.0,
                      process_tweet_text=None,
                      dry_run=False)
        bot.process_tweet(
            '{"data": {"text": "DOGE backwards is E GOD"}, "includes": {"media": [{"url": "..."}]}}')
        bot.process_tweet(
            '{"data": {"text": "Dodge coin is not what we need"}, "includes": {"media": [{"url": "..."}]}}')

    @patch.object(binance.client.Client, 'get_isolated_margin_account',
                  lambda _: {'userAssets': [{'asset': 'USDT', 'free': 12345}, {'asset': 'DOGE', 'free': 12345}]})
    @patch.object(binance.client.Client, 'get_orderbook_ticker', lambda _, symbol: {'askPrice': 0.05})
    @patch.object(binance.client.Client, 'get_max_margin_loan', lambda _, asset, isolatedSymbol: {'amount': 12345})
    @patch.object(binance.client.Client, 'create_margin_order', lambda _, **params: 'order_id')
    @patch.object(elonbot.ElonBot, 'get_image_text', lambda url: '')
    def test_isolated(self):
        bot = ElonBot('elonmusk', {'doge': 'DOGE', 'btc|bitcoin': 'BTC'}, 'USDT', 1, 2, True,
                      MarginType.ISOLATED_MARGIN,
                      2.0, process_tweet_text=None, dry_run=False)
        bot.process_tweet(
            '{"data": {"text": "DOGE backwards is E GOD"}, "includes": {"media": [{"url": "..."}]}}')
        bot.process_tweet(
            '{"data": {"text": "Dodge coin is not what we need"}, "includes": {"media": [{"url": "..."}]}}')
