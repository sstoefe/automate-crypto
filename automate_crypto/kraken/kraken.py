import os
import krakenex
from pykrakenapi import KrakenAPI


def krakenapi() -> KrakenAPI:
    """Initialize the KrakenAPI and use the given key and secret for private queries.

    Returns:
        KrakenAPI: KrakenAPI with access to private queries
    """
    api = krakenex.API(
        key=os.getenv("KRAKEN_API_KEY"), secret=os.getenv("KRAKEN_API_SECRET")
    )
    return KrakenAPI(api)
