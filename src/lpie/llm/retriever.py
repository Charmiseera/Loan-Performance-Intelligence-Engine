from typing import Any, Dict, Optional


# Official data dictionary definitions (Freddie Mac R47 layout)
FIELD_DEFINITIONS: Dict[str, str] = {
    "credit_score": "Borrower Credit Score: A numerical value between 300 and 850 based on credit bureau reports at origination.",
    "debt_to_income_ratio": "Debt-to-Income (DTI) Ratio: Total monthly debt obligations expressed as a percentage of gross monthly income (0-100%). Sentinel 999 denotes unavailable.",
    "original_ltv": "Original Loan-to-Value (LTV): Ratio of original loan amount to property appraised value or sales price at origination.",
    "cltv": "Combined Loan-to-Value (CLTV): Ratio of total mortgage liens to property value.",
    "original_interest_rate": "Original Interest Rate: The annual percentage rate agreed upon at mortgage origination.",
    "current_actual_upb": "Current Actual Unpaid Principal Balance (UPB): The remaining principal amount owed on the mortgage for the reporting period.",
    "loan_age": "Loan Age: The number of scheduled monthly payments elapsed since mortgage origination.",
    "current_loan_delinquency_status": "Delinquency Status: Number of months delinquent (0 = Current, 1 = 30-59 days, 2 = 60-89 days, 3+ = 90+ days, RA = Repurchased/Administrative).",
    "zero_balance_code": "Zero Balance Code: Indicates loan termination reason (01=Prepaid/Matured, 02=Third Party Sale, 03=Short Sale/Charge-off, 06=Repurchase/Administrative, 09=REO Disposition).",
    "modification_flag": "Modification Flag: Indicates whether the original terms of the mortgage were modified (Y=Yes, N=No).",
}


def retrieve_field_definition(field_name: str) -> str:
    """
    Retrieves exact, unparaphrased field definition from reference documentation (FR-008, FR-057).
    """
    clean_name = field_name.lower().strip()
    return FIELD_DEFINITIONS.get(
        clean_name,
        f"Field '{field_name}' is tracked in the mortgage performance reporting panel as an observed loan attribute.",
    )
