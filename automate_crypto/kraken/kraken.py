import os
import krakenex
import logging

from decimal import Decimal
from pykrakenapi import KrakenAPI
from typing import Tuple

from automate_crypto.util.util import setup_decimal, qDecimal


class Kraken:
    def __init__(self):
        self.api = KrakenAPI(
            krakenex.API(
                key=os.getenv("KRAKEN_API_KEY"), secret=os.getenv("KRAKEN_API_SECRET")
            )
        )
        self.q = setup_decimal(prec=16, decimal_prec="1.00000000")

    def _get_limit_percentage(self, limit_percentage: str) -> Decimal:
        """Get either the given limit percentage or default limit percentage.

        Args:
            limit_percentage (str): given limit percentage or None

        Returns:
            Decimal: limit percentage to use
        """
        if not limit_percentage:
            # use default percentage of 99.95%
            percentage = qDecimal(Decimal("0.9995"), self.q)
        else:
            # use given percentage
            percentage = qDecimal(Decimal(limit_percentage), self.q)
        return percentage

    def _calculate_limit_price(
        self,
        limit_price: str,
        limit_percentage: str,
        bid_price: Decimal,
    ) -> Decimal:
        """Calculate the limit price by calculating the (given) percentage of the bid price or use the given limit price.

        Args:
            limit_price (str): given limit price or None
            limit_percentage (str): given limit percentage or None
            bid_price (Decimal): bid price used for calculating the limit price

        Returns:
            Decimal: limit price
        """
        if not limit_price:
            # use percentage of bid price to calculate limit price
            percentage = self._get_limit_percentage(limit_percentage=limit_percentage)
            purchase_price = qDecimal(bid_price * percentage, self.q)
        else:
            # use given limit price
            purchase_price = qDecimal(Decimal(limit_price), self.q)

        return purchase_price

    def _calculate_limit_order(
        self,
        fiat_amount: Decimal,
        current_maker_fee: Decimal,
        limit_price: str,
        limit_percentage: str,
        bid_price: Decimal,
        price_precision: Decimal,
    ) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
        """Calculate all necessary information for a limit order.

        Args:
            fiat_amount (Decimal): amount of fiat money to spend
            current_maker_fee (Decimal): current maker fee
            limit_price (str): given limit price or None
            limit_percentage (str): given limit percentage or None
            bid_price (Decimal): bid price used for calculating the limit price
            price_precision (Decimal): price precision for the crypto asset

        Returns:
            Tuple[Decimal, Decimal, Decimal, Decimal]: purchase_volume, purchase_price, purchase_fiat, purchase_fee
        """

        purchase_price = self._calculate_limit_price(
            limit_price=limit_price,
            limit_percentage=limit_percentage,
            bid_price=bid_price,
        ).quantize(price_precision)
        purchase_fee = qDecimal(fiat_amount * current_maker_fee, self.q)
        purchase_fiat = qDecimal(fiat_amount - purchase_fee, self.q)
        purchase_volume = qDecimal(purchase_fiat / purchase_price, self.q)

        return purchase_volume, purchase_price, purchase_fiat, purchase_fee

    def _calculate_market_order(
        self,
        fiat_amount: Decimal,
        current_taker_fee: Decimal,
        ask_price: Decimal,
        price_precision: Decimal,
    ) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
        """Calculate all necessary information for a market order.

        Args:
            fiat_amount (Decimal): amount of fiat money to spend
            current_taker_fee (Decimal): current taker fee
            ask_price (Decimal): ask prcice used as market price
            price_precision (Decimal): price precision for the crypto asset

        Returns:
            Tuple[Decimal, Decimal, Decimal, Decimal]: purchase_volume, purchase_price, purchase_fiat, purchase_fee
        """
        purchase_price = qDecimal(ask_price, price_precision)

        purchase_fee = qDecimal(fiat_amount * current_taker_fee, self.q)
        purchase_fiat = qDecimal(fiat_amount - purchase_fee, self.q)
        purchase_volume = qDecimal(purchase_fiat / purchase_price, self.q)

        return purchase_volume, purchase_price, purchase_fiat, purchase_fee

    def _map_fee_currency_to_orderflags(self, fee_currency: str) -> str:
        """Map the given fee_currency to the corresponding orderflags.

        Args:
            fee_currency (str): 'fiat' or 'cyrpto'

        Returns:
            str: order flags
        """
        if fee_currency == "fiat":
            oflags = "fciq"
        elif fee_currency == "crypto":
            oflags = "fcib"
        else:
            oflags = ""
        return oflags

    def buy_crypto(
        self,
        pair: str,
        ordertype: str,
        limit_price: str,
        limit_percentage: str,
        fiat_amount: str,
        fee_currency: str,
        validate: bool,
    ):
        """Trigger crypto purchases on the kraken crypto exchange.

        Args:
            pair (str): tradeable-asset-pair, e.g. XXBTZEUR, XXBTZUSD, etc.
            ordertype (str): either 'limit' or 'market'
            limit_price (str): limit price for orders with ordertype 'limit'
            limit_percentage (str): limit percentage of the current bid price
            fiat_amount (str): amount of fiat money to spend
            fee_currency (str): select in which form to pay the fee ('crypto' or 'fiat')
            validate (bool): if true no order is placed
        """
        tradable_asset_pairs_information = self.api.get_tradable_asset_pairs(pair=pair)
        ordermin = qDecimal(tradable_asset_pairs_information["ordermin"][pair], self.q)
        pair_decimals = "1." + (
            "1" * tradable_asset_pairs_information["pair_decimals"][pair]
        )
        price_precision = Decimal(pair_decimals)

        _, _, fees_taker, fees_maker = self.api.get_trade_volume(
            pair=pair, fee_info=True
        )
        ticker_information = self.api.get_ticker_information(pair=pair)
        fiat_amount = qDecimal(Decimal(fiat_amount), self.q)

        if ordertype == "limit":
            bid_price = qDecimal(ticker_information["b"][pair][0], self.q)
            current_maker_fee = qDecimal(str(fees_maker[pair]["fee"]), self.q) / 100
            (
                purchase_volume,
                purchase_price,
                purchase_fiat,
                purchase_fee,
            ) = self._calculate_limit_order(
                fiat_amount=fiat_amount,
                current_maker_fee=current_maker_fee,
                limit_price=limit_price,
                limit_percentage=limit_percentage,
                bid_price=bid_price,
                price_precision=price_precision,
            )
        elif ordertype == "market":
            ask_price = qDecimal(ticker_information["a"][pair][0], self.q)
            current_taker_fee = qDecimal(str(fees_taker[pair]["fee"]), self.q) / 100
            (
                purchase_volume,
                purchase_price,
                purchase_fiat,
                purchase_fee,
            ) = self._calculate_market_order(
                fiat_amount=fiat_amount,
                current_taker_fee=current_taker_fee,
                ask_price=ask_price,
            )
        else:
            logging.error(f"Unsupported ordertype: {ordertype}")

        if purchase_volume < ordermin:
            logging.error(
                f"Can't place order since minimum order volume for {pair} is not met! Minimum order volume: {ordermin}, actual oder volume: {purchase_volume}."
            )
            exit()

        oflags = self._map_fee_currency_to_orderflags(fee_currency=fee_currency)

        response = self.api.add_standard_order(
            pair=pair,
            type="buy",
            ordertype=ordertype,
            volume=purchase_volume,
            price=purchase_price,
            validate=validate,
            oflags=oflags,
        )

        if validate:
            print(f"{response=}")
            print(
                f"buying {purchase_volume} {pair} @ {ordertype}, price {purchase_price}"
            )
            print(
                f"{fiat_amount=}, {purchase_fee=}, {purchase_fiat=}, {purchase_fee + purchase_fiat=}"
            )
        else:
            order = response["descr"]["order"]
            txid = f", txid={response['txid']}" if "txid" in response else ""
            logging.info(f"{order}{txid}")

    def withdraw_crypto(
        self,
        asset: str,
        amount: str,
        max_fee: str,
        withdrawal_key: str,
        validate: bool,
    ):
        """Trigger crypto withdrawals to a withdrawal wallet on the kraken crypto exchange.

        Args:
            asset (str): crypto asset, e.g. XBT, ETH, etc.
            amount (str): amount of crypto to withdraw
            max_fee (str):  max fee to pay (in %)
            withdrawal_key (str): withdrawal address (needs to be setup in the kraken account)
            validate (bool): if true no withdrawal is triggered
        """
        withdrawal_info = self.api.get_withdrawal_information(
            key=withdrawal_key, asset=asset, amount=float(amount)
        )

        withdraw_fee = qDecimal(withdrawal_info[asset]["fee"], self.q)
        if not amount:
            amount = withdrawal_info[asset]["limit"]
        amount = qDecimal(amount, self.q)
        withdraw_amount = qDecimal(amount - withdraw_fee, self.q)
        max_fee = qDecimal(max_fee, self.q)
        fee_to_pay = qDecimal(withdraw_fee / amount * 100, self.q)

        if not validate:
            if fee_to_pay <= max_fee:
                refid = self.api.withdraw_funds(
                    key=withdrawal_key, asset=asset, amount=float(amount)
                )
                logging.info(
                    f"fee={fee_to_pay}% <= max_fee={max_fee}%: withdraw {withdraw_amount} {asset} to '{withdrawal_key}', refid={refid}"
                )
            else:
                logging.warning(
                    f"fee={fee_to_pay}% > max_fee={max_fee}%: no withdrawal was triggered."
                )
        else:
            print(f"withdraw will get triggered: {fee_to_pay <= max_fee}")
            print(f"{fee_to_pay=}, {max_fee=}")
