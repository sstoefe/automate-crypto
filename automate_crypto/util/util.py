from decimal import Decimal, getcontext
from typing import Union


def qDecimal(decimal: Union[str, Decimal], q: Decimal) -> Decimal:
    """Ensure that the given decimal is created as Decimal and is quantized to the correct precision.

    Args:
        decimal (Union[str, Decimal]): decimal to quantize
        q (Decimal): Decimal used for quantization

    Raises:
        ValueError: if decimal parameter is not of type str or Decimal

    Returns:
        [Decimal]: the given Decimal but quantized
    """
    if isinstance(decimal, Decimal):
        return decimal.quantize(q)
    elif isinstance(decimal, str):
        return Decimal(decimal).quantize(q)
    else:
        raise ValueError(f"Unsupported decimal type {type(decimal)}")


def setup_decimal(
    prec: int = 16, rounding: str = "ROUND_FLOOR", decimal_prec: str = "1.00000000"
) -> Decimal:
    """Configure the decimal settings and set the precision and rounding strategy.

    Args:
        prec (int, optional): precision of the decimal module. Defaults to 16.
        rounding (str, optional): rounding strategy of the decimal module. Defaults to "ROUND_FLOOR".
        decimal_prec (str, optional): precision for quantization. Defaults to "1.00000000".

    Returns:
        Decimal: quantization precision
    """
    getcontext().prec = prec
    getcontext().rounding = rounding
    return Decimal(decimal_prec)
