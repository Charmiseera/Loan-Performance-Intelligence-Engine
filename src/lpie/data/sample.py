from dataclasses import dataclass, field
from typing import Dict, List, Set
import numpy as np
import pandas as pd


@dataclass
class StratifiedSamplingResult:
    sampled_loan_ids: Set[str]
    sampling_weights: Dict[str, float]
    total_population_loans: int
    sampled_loans_count: int
    vintage_breakdown: Dict[int, Dict[str, int]]


def compute_whole_loan_sample(
    loan_inventory: pd.DataFrame,
    target_total_loans: int = 60000,
    retain_all_credit_events: bool = True,
    seed: int = 42,
) -> StratifiedSamplingResult:
    """
    Compute a two-level stratified sample of loans.
    Guarantees:
    1. Sample is strictly at whole-loan level (Principle II, FR-006).
    2. All rare credit events are retained if retain_all_credit_events=True.
    3. Non-event loans are stratified proportionately across vintages.
    4. Exact sampling weights / inverse inclusion probabilities are recorded per loan.
    """
    rng = np.random.default_rng(seed)
    total_pop = len(loan_inventory)
    
    if total_pop <= target_total_loans:
        all_ids = set(loan_inventory["loan_id"].tolist())
        weights = {lid: 1.0 for lid in all_ids}
        return StratifiedSamplingResult(
            sampled_loan_ids=all_ids,
            sampling_weights=weights,
            total_population_loans=total_pop,
            sampled_loans_count=total_pop,
            vintage_breakdown={},
        )

    sampled_ids: Set[str] = set()
    weights: Dict[str, float] = {}
    vintage_stats: Dict[int, Dict[str, int]] = {}

    # Step 1: Separate credit events and non-events
    if retain_all_credit_events and "is_credit_event" in loan_inventory.columns:
        event_df = loan_inventory[loan_inventory["is_credit_event"] == True]
        non_event_df = loan_inventory[loan_inventory["is_credit_event"] == False]
        
        event_ids = set(event_df["loan_id"].tolist())
        sampled_ids.update(event_ids)
        for lid in event_ids:
            weights[lid] = 1.0  # Selected with probability 1.0
            
        remaining_slots = max(0, target_total_loans - len(event_ids))
    else:
        non_event_df = loan_inventory
        remaining_slots = target_total_loans

    # Step 2: Stratify non-events by vintage
    if "vintage" in non_event_df.columns:
        vintages = sorted(non_event_df["vintage"].unique())
        total_non_events = len(non_event_df)
        
        for v in vintages:
            v_subset = non_event_df[non_event_df["vintage"] == v]
            v_count = len(v_subset)
            
            # Allocation proportional to vintage size
            v_target = int(np.round((v_count / total_non_events) * remaining_slots))
            v_target = min(v_target, v_count)
            
            if v_target > 0:
                v_sampled_idx = rng.choice(v_subset.index, size=v_target, replace=False)
                v_sampled_ids = v_subset.loc[v_sampled_idx, "loan_id"].tolist()
                sampled_ids.update(v_sampled_ids)
                
                # Weight = population / sample (inverse inclusion probability)
                inclusion_prob = v_target / v_count
                weight_val = 1.0 / inclusion_prob if inclusion_prob > 0 else 1.0
                
                for lid in v_sampled_ids:
                    weights[lid] = float(weight_val)
                    
                vintage_stats[int(v)] = {
                    "population": int(v_count),
                    "sampled": int(v_target),
                }
    else:
        # Simple random sample of remaining
        sampled_idx = rng.choice(non_event_df.index, size=min(remaining_slots, len(non_event_df)), replace=False)
        for lid in non_event_df.loc[sampled_idx, "loan_id"].tolist():
            sampled_ids.add(lid)
            weights[lid] = float(len(non_event_df) / len(sampled_idx))

    return StratifiedSamplingResult(
        sampled_loan_ids=sampled_ids,
        sampling_weights=weights,
        total_population_loans=total_pop,
        sampled_loans_count=len(sampled_ids),
        vintage_breakdown=vintage_stats,
    )
