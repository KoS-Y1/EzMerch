#
# Created by y1 on 2026-10-11
#

import argparse
import math


def positive_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero") from None
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return number


def nonnegative_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a finite number greater than or equal to zero") from None
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than or equal to zero")
    return number


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer greater than zero") from None
    if number <= 0:
        raise argparse.ArgumentTypeError("must be an integer greater than zero")
    return number


