import pandas as pd
import pytest
from lpie.data.decode import decode_categorical_fields, get_documented_decodes


def test_decode_categorical_fields():
    df = pd.DataFrame({
        "channel": ["R", "B", "C"],
        "occupancy_status": ["P", "I", "S"],
        "loan_purpose": ["P", "C", "N"],
    })
    
    decode_maps = {
        "channel": {"R": "Retail", "B": "Broker", "C": "Correspondent"},
        "occupancy_status": {"P": "Primary", "I": "Investment", "S": "Second Home"},
    }
    
    decoded_df = decode_categorical_fields(df, decode_maps)
    assert decoded_df["channel"].tolist() == ["Retail", "Broker", "Correspondent"]
    assert decoded_df["occupancy_status"].tolist() == ["Primary", "Investment", "Second Home"]
    assert decoded_df["loan_purpose"].tolist() == ["P", "C", "N"]  # Unmapped column unchanged


def test_decode_categorical_unknown_handling():
    df = pd.DataFrame({"channel": ["R", "UNKNOWN_CODE"]})
    decode_maps = {"channel": {"R": "Retail"}}
    
    # Should keep original value if unknown
    decoded_df = decode_categorical_fields(df, decode_maps, keep_unmapped=True)
    assert decoded_df["channel"].tolist() == ["Retail", "UNKNOWN_CODE"]
