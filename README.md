# Automate your crypto purchases

I created this program because I was missing the feature of a monthly saving plan for crypto currencies on the most common crypto exchanges.
At the moment only the kraken crypto exchange is supported.

## What can this script do?
It allows you to programatically create order or withdrawal requests on the kraken crypto exchange.

## How to run the script
Install `automate-crypto` and its dependencies:
```
poetry install
```
Now you can run the program:
```
automate-crypto <exchange> <action> <action-options>
```
For example:
```
# place a limit order for bitcoin with a fixed limit-price
automate-crypto kraken buy --pair XXBTZUSD --amount 100.0 --fee-currency fiat --ordertype limit --limit-price 35000.0

# place a limit order for bitcoin with a percental (97.5%) of the current bid-price
automate-crypto kraken buy --pair XXBTZUSD --amount 100.0 --fee-currency fiat --ordertype limit --limit-percentage 0.
975
# place a limit order for bitcoin with default limit percentage (99.95%)
automate-crypto kraken buy --pair XXBTZEUR --amount 100.0 --fee-currency fiat --ordertype limit

# withdraw all bitcoin you have to your wallet (if fee to pay is less than max-fee (0.5%))
automate-crypto kraken withdraw --asset XBT --withdrawal-key "withdrawal address (needs to be setup in the kraken account)" --max-fee 0.5 
```