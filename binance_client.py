import math
from decimal import Decimal
from enum import Enum
from typing import Optional, Tuple

import binance.client

from utils import log

QUANTITY_RESOLUTION = {
    'BTC': 6,
    'DOGE': 0
}


def floor(value: Decimal, digit: int) -> Decimal:
    shift = (10 ** digit)
    return math.floor(value * shift) / shift


class MarginType(Enum):
    CROSS_MARGIN = 'cross_margin'
    ISOLATED_MARGIN = 'isolated_margin'


class Binance:
    def __init__(self, margin_type: MarginType, key: str, secret: str,
                 dry_run=False):
        self.client = binance.client.Client(key, secret)
        self.margin_type = margin_type
        self.dry_run = dry_run

    def get_available_asset(self, asset: str, ticker: str) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        if self.margin_type == MarginType.CROSS_MARGIN:
            asset_value, ticker_value = None, None
            for a in self.client.get_margin_account()['userAssets']:
                if a['asset'] == asset:
                    asset_value = Decimal(a['free'])
                if a['asset'] == ticker:
                    ticker_value = Decimal(a['free'])
            return asset_value, ticker_value
        else:
            for a in self.client.get_isolated_margin_account()['assets']:
                if a['baseAsset']['asset'] == ticker and a['quoteAsset']['asset'] == asset:
                    return Decimal(a['quoteAsset']['free']), Decimal(a['baseAsset']['free'])
            return None, None

    def get_ask_price(self, ticker: str, asset: str) -> Decimal:
        pair = ticker + asset
        return Decimal(self.client.get_orderbook_ticker(symbol=pair)['askPrice'])

    def get_max_borrowable(self, asset: str, ticker: str) -> Decimal:
        pair = ticker + asset
        if self.margin_type == MarginType.CROSS_MARGIN:
            return Decimal(self.client.get_max_margin_loan(asset=asset)['amount'])
        else:
            return Decimal(
                self.client.get_max_margin_loan(asset=asset, isolatedSymbol=pair)['amount'])

    def buy(self, amount: Decimal, ticker: str, asset: str) -> str:
        pair = ticker + asset
        log('Buying', ticker, floor(amount, QUANTITY_RESOLUTION[ticker]), pair)
        amount = floor(amount, QUANTITY_RESOLUTION[ticker])
        order = f'create_margin_order(symbol="{pair}", side=Client.SIDE_BUY, type=Client.ORDER_TYPE_MARKET, ' \
                f'quantity={amount}, sideEffectType="MARGIN_BUY")'
        log(order)
        if self.dry_run:
            return order
        order = self.client.create_margin_order(
            symbol=pair,
            side=binance.client.Client.SIDE_BUY,
            type=binance.client.Client.ORDER_TYPE_MARKET,
            quantity=amount,
            sideEffectType="MARGIN_BUY",
            isIsolated=self.margin_type == MarginType.ISOLATED_MARGIN)
        log('Buying', ticker, order)
        return order

    def sell(self, amount: Decimal, ticker: str, asset: str) -> str:
        pair = ticker + asset
        amount = floor(amount, QUANTITY_RESOLUTION[ticker])
        order = f'create_margin_order(symbol="{pair}", side=Client.SIDE_SELL, type=Client.ORDER_TYPE_MARKET, ' \
                f'sideEffectType="AUTO_REPAY", quantity={amount})'
        log(order)
        if self.dry_run:
            return order
        order = self.client.create_margin_order(
            symbol=pair,
            side=binance.client.Client.SIDE_SELL,
            type=binance.client.Client.ORDER_TYPE_MARKET,
            sideEffectType="AUTO_REPAY",
            quantity=amount,
            isIsolated=self.margin_type == MarginType.ISOLATED_MARGIN)
        log('Selling', ticker, order)
        return order
