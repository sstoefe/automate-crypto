import argparse
import logging
import toml

from dotenv import load_dotenv
from pathlib import Path

from automate_crypto.kraken.kraken import Kraken


KRAKEN = "kraken"
BUY = "buy"
WITHDRAW = "withdraw"


def main():
    if Path("config.toml").exists():
        config = toml.load("config.toml")
        env_file = (
            Path(config["automate-crypto"]["env_file"])
            if config["automate-crypto"]["env_file"]
            else Path(".env")
        )
        logging_path = (
            Path(config["automate-crypto"]["logging_path"])
            if config["automate-crypto"]["logging_path"]
            else Path("automate_crypto.log")
        )
    else:
        env_file = Path(".env")
        logging_path = Path("automate_crypto.log")

    load_dotenv(env_file)

    logging.basicConfig(
        filename=logging_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    )

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="supported crypto exchanges",
        help="crypto exchanges with API access",
        dest="exchange",
    )

    kraken_parser = subparsers.add_parser(KRAKEN)
    kraken_subparsers = kraken_parser.add_subparsers(
        title="actions",
        help="supported actions (either 'buy' or 'withdraw'",
        dest="action",
    )

    kraken_buy = kraken_subparsers.add_parser(BUY)
    kraken_buy.add_argument(
        "--pair",
        type=str,
        help="the ticker pair (e.g. 'XXBTZUSD')",
        required=True,
    )
    kraken_buy.add_argument(
        "--ordertype",
        type=str,
        choices=["market", "limit"],
        help="the ordertype (either 'market' order or 'limit' order)",
        required=False,
        default="limit",
    )
    kraken_buy.add_argument(
        "--limit-price",
        type=str,
        help="the limit price for orders with ordertype 'limit'",
        required=False,
        default=None,
    )
    kraken_buy.add_argument(
        "--limit-percentage",
        type=str,
        help="the limit percentage of the current bid price",
        required=False,
        default=None,
    )
    kraken_buy.add_argument(
        "--amount",
        type=str,
        help="amount of fiat money you want to spend",
        required=True,
    )
    kraken_buy.add_argument(
        "--fee-currency",
        type=str,
        choices=["crypto", "fiat"],
        help="",
        required=False,
        default="fiat",
    )
    kraken_buy.add_argument(
        "--validate",
        action="store_true",
        help="only for validation (does not place an order)",
    )

    kraken_withdraw = kraken_subparsers.add_parser(WITHDRAW)
    kraken_withdraw.add_argument(
        "--asset",
        type=str,
        help="crypto asset you want to withdraw (e.g. 'XBT')",
        required=True,
    )
    kraken_withdraw.add_argument(
        "--amount",
        type=str,
        help="amount of crypto you want to withdraw",
        required=False,
        default=0.0,
    )
    kraken_withdraw.add_argument(
        "--withdrawal-key",
        type=str,
        help="withdrawal key name, as set up on your kraken account",
        required=True,
    )
    kraken_withdraw.add_argument(
        "--max-fee",
        type=str,
        help="maximum withdraw fee in % that you are willing to pay",
        default="0.5",
    )
    kraken_withdraw.add_argument(
        "--validate",
        action="store_true",
        help="only for validation (does not place a withdrawal request)",
    )

    args = parser.parse_args()

    if args.exchange == KRAKEN:
        kraken = Kraken()
        if args.action == BUY:
            kraken.buy_crypto(
                pair=args.pair,
                ordertype=args.ordertype,
                limit_price=args.limit_price,
                limit_percentage=args.limit_percentage,
                fiat_amount=args.amount,
                fee_currency=args.fee_currency,
                validate=args.validate,
            )
        elif args.action == WITHDRAW:
            kraken.withdraw_crypto(
                asset=args.asset,
                amount=args.amount,
                max_fee=args.max_fee,
                withdrawal_key=args.withdrawal_key,
                validate=args.validate,
            )
        else:
            logging.error(
                f"Unsupported action {args.action} for kraken. This should never happen."
            )
    else:
        logging.error(
            f"Unsupported crypto exchange {args.exchange}. This should never happen."
        )


if __name__ == "__main__":
    main()
