import os
import krakenex
import logging

from decimal import Decimal
from pykrakenapi import KrakenAPI

from automate_crypto.util.util import setup_decimal, qDecimal


def krakenapi() -> KrakenAPI:
    """Initialize the KrakenAPI and use the given key and secret for private queries.

    Returns:
        KrakenAPI: KrakenAPI with access to private queries
    """
    api = krakenex.API(
        key=os.getenv("KRAKEN_API_KEY"), secret=os.getenv("KRAKEN_API_SECRET")
    )
    return KrakenAPI(api)


def buy_crypto(pair: str, ordertype: str, amount: str, oflags: str, validate: bool):
    """Supports crypto purchases on the kraken crypto exchange.

    Args:
        pair (str): tradeable-asset-pair, e.g. XXBTZEUR, XXBTZUSD, etc.
        ordertype (str): either 'limit' or 'market'
        amount (str): amount of fiat money to spend
        oflags (str): additional order flags ('post', 'fcib', 'fciq', 'nompp')
        validate (bool): if true no order is placed
    """
    q = setup_decimal(prec=16, decimal_prec="1.00000000")
    kraken = krakenapi()

    _, _, _, fees_maker = kraken.get_trade_volume(pair=pair, fee_info=True)
    tradable_asset_pairs_information = kraken.get_tradable_asset_pairs(pair=pair)
    ticker_information = kraken.get_ticker_information(pair=pair)

    ordermin = qDecimal(tradable_asset_pairs_information["ordermin"][pair], q)
    pair_decimals = "1." + (
        "1" * tradable_asset_pairs_information["pair_decimals"][pair]
    )
    price_precision = Decimal(pair_decimals)

    bid_price = qDecimal(ticker_information["b"][pair][0], q)
    limit_price = qDecimal(bid_price * Decimal("0.9995"), q)
    limit_price_prec = qDecimal(limit_price, price_precision)

    fiat_amount = qDecimal(amount, q)
    current_maker_fee = qDecimal(str(fees_maker[pair]["fee"]), q) / 100
    fee_to_pay = qDecimal(fiat_amount * current_maker_fee, q)
    purchase_fiat = qDecimal(fiat_amount - fee_to_pay, q)
    purchase_volume = qDecimal(purchase_fiat / limit_price_prec, q)

    if purchase_volume < ordermin:
        logging.error(
            f"Can't place order since minimum order volume for {pair} is not met! Minimum order volume: {ordermin}, actual oder volume: {purchase_volume}."
        )
        exit()

    response = kraken.add_standard_order(
        pair=pair,
        type="buy",
        ordertype=ordertype,
        volume=purchase_volume,
        price=limit_price_prec,
        validate=validate,
        oflags=oflags,
    )

    if validate:
        print(response)
    else:
        order = response["descr"]["order"]
        txid = f", txid={response['txid']}" if "txid" in response else ""
        logging.info(f"{order}{txid}")
