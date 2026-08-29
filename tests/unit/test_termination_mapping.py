import pandas as pd
import pytest
from lpie.labels.termination import classify_zero_balance_code, TerminationClass


def test_zero_balance_code_classification():
    # Credit events (02, 03, 09, 15)
    assert classify_zero_balance_code("02") == TerminationClass.CREDIT_EVENT
    assert classify_zero_balance_code("03") == TerminationClass.CREDIT_EVENT
    assert classify_zero_balance_code("09") == TerminationClass.CREDIT_EVENT
    assert classify_zero_balance_code("15") == TerminationClass.CREDIT_EVENT

    # Prepayment (01)
    assert classify_zero_balance_code("01") == TerminationClass.PREPAYMENT

    # Administrative removals (16, 96)
    assert classify_zero_balance_code("16") == TerminationClass.REMOVE
    assert classify_zero_balance_code("96") == TerminationClass.REMOVE

    # Active / Blank
    assert classify_zero_balance_code("") == TerminationClass.ACTIVE
    assert classify_zero_balance_code(None) == TerminationClass.ACTIVE
