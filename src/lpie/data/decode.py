from typing import Any, Dict
import pandas as pd


def decode_categorical_fields(
    df: pd.DataFrame,
    decode_maps: Dict[str, Dict[str, str]],
    keep_unmapped: bool = True,
) -> pd.DataFrame:
    """
    Decode single/multi-character categorical codes to human-readable strings.
    """
    df_decoded = df.copy()
    for col, mapping in decode_maps.items():
        if col in df_decoded.columns and mapping:
            if keep_unmapped:
                df_decoded[col] = df_decoded[col].map(lambda x: mapping.get(str(x), x) if pd.notna(x) else x)
            else:
                df_decoded[col] = df_decoded[col].map(mapping)
    return df_decoded


def get_documented_decodes(schema_config: Any) -> Dict[str, Dict[str, str]]:
    """Extract all decodes from schema configuration."""
    decodes: Dict[str, Dict[str, str]] = {}
    for f in getattr(schema_config, "origination_fields", []):
        if f.decodes:
            decodes[f.name] = f.decodes
    for f in getattr(schema_config, "performance_fields", []):
        if f.decodes:
            decodes[f.name] = f.decodes
    return decodes
