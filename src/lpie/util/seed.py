import hashlib
import random
import numpy as np


def derive_child_seed(root_seed: int, stage_name: str) -> int:
    """
    Derive a deterministic 31-bit child seed from a root seed and stage name.
    Ensures stages have isolated, deterministic pseudo-random sequences without global state leakage.
    """
    hash_input = f"{root_seed}:{stage_name}".encode("utf-8")
    digest = hashlib.sha256(hash_input).hexdigest()
    # Mask to positive 31-bit integer for maximum compatibility with numpy/scipy/lightgbm/xgboost
    return int(digest[:8], 16) & 0x7FFFFFFF


def set_global_seed(seed: int) -> None:
    """Set global seeds for standard random and numpy as fallback."""
    random.seed(seed)
    np.random.seed(seed)
