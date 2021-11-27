import os
import krakenex
import logging
import pandas as pd

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


def withdraw_crypto(
    asset: str,
    amount: str,
    max_fee: str,
    key: str,
    validate: bool,
):
    """Supports crypto withdrawals to a withdrawal wallet on the kraken crypto exchange.

    Args:
        asset (str): crypto asset, e.g. XBT, ETH, etc.
        amount (str): amount of crypto to withdraw
        max_fee (str): max fee to pay (in %)
        key (str): withdrawal address (needs to be setup in the kraken account)
        validate (bool): if true no withdrawal is triggered
    """
    q = setup_decimal(prec=16, decimal_prec="1.00000000")
    kraken = krakenapi()

    # withdrawal_information = kraken.get_withdrawal_information(key=key, asset=asset, amount=float(amount))
    result = {
        "method": "Bitcoin",
        "limit": "0.00700",
        "amount": "0.00685",
        "fee": "0.00015000",
    }
    withdrawal_info = pd.DataFrame(index=[asset], data=result).T
    withdraw_fee = qDecimal(withdrawal_info[asset]["fee"], q)
    if not amount:
        amount = withdrawal_info[asset]["limit"]
    amount = qDecimal(amount, q)
    withdraw_amount = qDecimal(amount - withdraw_fee, q)
    max_fee = qDecimal(max_fee, q)
    fee_to_pay = qDecimal(withdraw_fee / amount * 100, q)

    if not validate:
        if fee_to_pay <= max_fee:
            # refid = kraken.withdraw_funds(key=key, asset=asset, amount=float(amount))
            refid = "AGBSO6T-UFMTTQ-I7KGS6"
            logging.info(
                f"fee={fee_to_pay}% <= max_fee={max_fee}%: withdraw {withdraw_amount} {asset} to '{key}', refid={refid}"
            )
        else:
            logging.warning(
                f"fee={fee_to_pay}% > max_fee={max_fee}%: no withdrawal was triggered."
            )
    else:
        print(f"withdraw will get triggered: {fee_to_pay <= max_fee}")
        print(f"{fee_to_pay=}, {max_fee=}")
