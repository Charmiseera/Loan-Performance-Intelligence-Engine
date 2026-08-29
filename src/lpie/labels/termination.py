from enum import Enum
from typing import Optional
import pandas as pd


class TerminationClass(str, Enum):
    PREPAYMENT = "PREPAYMENT"
    CREDIT_EVENT = "CREDIT_EVENT"
    REMOVE = "REMOVE"
    ACTIVE = "ACTIVE"


def classify_zero_balance_code(code: Optional[str]) -> TerminationClass:
    """
    Classify Freddie Mac Zero Balance Code (performance field 9) into outcome categories.
    Rules:
    - 01: Prepayment (voluntary payoff / maturation)
    - 02, 03, 09, 15: Credit Event (Third party sale, short sale, REO, note sale)
    - 16, 96: Administrative removals (RPL securitization, defect repurchase) -> remove from label set
    - blank / nan: Active / Censored
    """
    if code is None or pd.isna(code):
        return TerminationClass.ACTIVE
    
    c_str = str(code).strip().zfill(2)
    if c_str == "01":
        return TerminationClass.PREPAYMENT
    elif c_str in ("02", "03", "09", "15"):
        return TerminationClass.CREDIT_EVENT
    elif c_str in ("16", "96"):
        return TerminationClass.REMOVE
    elif c_str in ("", "00", "nan"):
        return TerminationClass.ACTIVE
    else:
        # Default unclassified non-empty codes
        return TerminationClass.ACTIVE
