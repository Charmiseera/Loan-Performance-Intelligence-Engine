import pytest
from lpie.util.seed import derive_child_seed, set_global_seed


def test_derive_child_seed_deterministic():
    root_seed = 42
    seed_a1 = derive_child_seed(root_seed, "ingest")
    seed_a2 = derive_child_seed(root_seed, "ingest")
    assert seed_a1 == seed_a2, "Child seed must be deterministic for identical (root_seed, stage_name)"


def test_derive_child_seed_distinct_across_stages():
    root_seed = 42
    seed_ingest = derive_child_seed(root_seed, "ingest")
    seed_train = derive_child_seed(root_seed, "train")
    assert seed_ingest != seed_train, "Different stages must receive distinct child seeds"


def test_derive_child_seed_distinct_across_root_seeds():
    seed1 = derive_child_seed(42, "train")
    seed2 = derive_child_seed(43, "train")
    assert seed1 != seed2, "Different root seeds must produce different child seeds"


def test_derive_child_seed_valid_range():
    seed = derive_child_seed(42, "features")
    assert isinstance(seed, int)
    assert 0 <= seed < (2**31 - 1), "Child seed must be a valid 32-bit positive integer"
