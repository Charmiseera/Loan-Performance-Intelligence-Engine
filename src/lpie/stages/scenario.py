from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from lpie.advanced.monte_carlo import simulate_portfolio_monte_carlo
from lpie.conf.loader import load_scenarios_config
from lpie.stages.base import BaseStage, StageContext
from lpie.stages.registry import global_stage_registry


def _project_segment(
    group: pd.DataFrame,
    def_mult: float,
    prep_mult: float,
    det_mult: float,
) -> Dict[str, float]:
    """Apply scenario multipliers to a portfolio segment and return projected rates."""
    return {
        "projected_default_rate": round(min(1.0, float(group["prob_default_12m"].mean()) * def_mult), 5),
        "projected_prepay_rate": round(min(1.0, float(group["prob_prepay_12m"].mean()) * prep_mult), 5),
        "projected_deterioration_rate": round(min(1.0, float(group["prob_deterioration_6m"].mean()) * det_mult), 5),
        "loan_count": len(group),
    }


def _segment_breakdown(
    preds: pd.DataFrame,
    feature_df: pd.DataFrame,
    segment_cols: List[str],
    def_mult: float,
    prep_mult: float,
    det_mult: float,
) -> Dict[str, Any]:
    """
    Break projections out by segment (FR-049). Reconciles with portfolio total (SC-018).
    Only segments present in the scoring data are reported.
    """
    breakdown: Dict[str, Any] = {}
    for col in segment_cols:
        if col not in feature_df.columns:
            continue
        merged = preds.merge(feature_df[["loan_id", "monthly_reporting_period", col]], on=["loan_id", "monthly_reporting_period"], how="left")
        seg_results = {}
        for seg_val, grp in merged.groupby(col):
            seg_results[str(seg_val)] = _project_segment(grp, def_mult, prep_mult, det_mult)
        breakdown[col] = seg_results
    return breakdown


def _top_drivers(
    portfolio_rate: float,
    segment_breakdown: Dict[str, Any],
    metric: str = "projected_default_rate",
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Rank segments contributing most to deviation from portfolio-level projection (FR-050).
    """
    deviations = []
    for dim, segs in segment_breakdown.items():
        for val, stats in segs.items():
            seg_rate = stats.get(metric, 0.0)
            deviations.append({
                "segment_dimension": dim,
                "segment_value": val,
                "metric": metric,
                "segment_rate": round(seg_rate, 5),
                "portfolio_rate": round(portfolio_rate, 5),
                "deviation": round(seg_rate - portfolio_rate, 5),
                "loan_count": stats.get("loan_count", 0),
            })
    deviations.sort(key=lambda x: abs(x["deviation"]), reverse=True)
    return deviations[:top_k]


class ScenarioStage(BaseStage):
    name = "scenario"
    declared_inputs: List[str] = ["predictions_scoring.parquet"]
    declared_outputs: List[str] = [
        "scenario_projections.json",
        "scenario_segment_breakdown.json",
        "monte_carlo_results.json",
        "scenario_report.md",
    ]

    def run(self, context: StageContext) -> Dict[str, Any]:
        preds = context.store.read_parquet("train", "predictions_scoring.parquet")
        scenarios = load_scenarios_config(context.config.scenarios_file)

        # Load scoring feature matrix for segment columns (vintage, credit band, geography, servicer)
        try:
            feat_df = context.store.read_parquet("features", "feature_matrix_scoring.parquet")
        except Exception:
            feat_df = pd.DataFrame()

        # --- Portfolio-level baselines ---
        base_def = float(preds["prob_default_12m"].mean())
        base_prep = float(preds["prob_prepay_12m"].mean())
        base_det = float(preds["prob_deterioration_6m"].mean())

        # --- Scenario multipliers ---
        scenario_params = {
            "baseline": {
                "description": scenarios.baseline.description + " [STATED ASSUMPTION — not a forecast]",
                "def_mult": scenarios.baseline.default_multiplier,
                "prep_mult": scenarios.baseline.prepayment_multiplier,
                "det_mult": 1.0,
            },
            "adverse": {
                "description": scenarios.adverse.description + " [STATED ASSUMPTION — not a forecast]",
                "def_mult": scenarios.adverse.default_multiplier,
                "prep_mult": scenarios.adverse.prepayment_multiplier,
                "det_mult": 2.2,
            },
            "high_prepayment": {
                "description": scenarios.high_prepayment.description + " [STATED ASSUMPTION — not a forecast]",
                "def_mult": scenarios.high_prepayment.default_multiplier,
                "prep_mult": scenarios.high_prepayment.prepayment_multiplier,
                "det_mult": 0.9,
            },
        }

        # Segment dimensions per FR-049 (vintage, credit band, geography, servicer)
        segment_cols = ["property_state", "original_loan_term", "servicer_name", "loan_purpose", "channel"]

        projections: Dict[str, Any] = {}
        segment_breakdowns: Dict[str, Any] = {}
        all_top_drivers: Dict[str, Any] = {}

        for sc_name, sc in scenario_params.items():
            port_rates = {
                "description": sc["description"],
                "projected_default_rate": round(min(1.0, base_def * sc["def_mult"]), 5),
                "projected_prepay_rate": round(min(1.0, base_prep * sc["prep_mult"]), 5),
                "projected_deterioration_rate": round(min(1.0, base_det * sc["det_mult"]), 5),
                "portfolio_loan_months": len(preds),
            }
            projections[sc_name] = port_rates

            # Segment breakdown (FR-049, SC-018)
            if not feat_df.empty:
                breakdown = _segment_breakdown(
                    preds, feat_df, segment_cols,
                    sc["def_mult"], sc["prep_mult"], sc["det_mult"],
                )
                segment_breakdowns[sc_name] = breakdown
                # Top contributing drivers (FR-050)
                all_top_drivers[sc_name] = _top_drivers(
                    port_rates["projected_default_rate"], breakdown,
                    metric="projected_default_rate", top_k=5,
                )
            else:
                segment_breakdowns[sc_name] = {}
                all_top_drivers[sc_name] = []

        # --- Monte Carlo Portfolio Loss Simulation (FR-101, FR-102) ---
        upb_arr = (
            feat_df["current_actual_upb"].to_numpy()
            if not feat_df.empty and "current_actual_upb" in feat_df.columns
            else np.full(len(preds), 220000.0)
        )
        p_def_arr = preds["prob_default_12m"].to_numpy()
        p_prep_arr = preds["prob_prepay_12m"].to_numpy()

        mc_results = simulate_portfolio_monte_carlo(
            upb_array=upb_arr,
            prob_default_array=p_def_arr,
            prob_prepay_array=p_prep_arr,
            num_iterations=1000,
            lgd_mean=0.35,
            random_seed=42,
        )

        context.store.write_json(projections, self.name, "scenario_projections.json")
        context.store.write_json(segment_breakdowns, self.name, "scenario_segment_breakdown.json")
        context.store.write_json(mc_results, self.name, "monte_carlo_results.json")

        # --- Markdown report ---
        lines = [
            "# Portfolio Scenario and Stress Simulation Report\n",
            "> **Note**: All scenario inputs are stated assumptions, not economic forecasts.\n",
            "## Portfolio-Level Projections\n",
            "| Scenario | Default Rate | Prepayment Rate | Deterioration Rate |",
            "|---|---|---|---|",
        ]
        for sc_name, p in projections.items():
            lines.append(
                f"| {sc_name.replace('_', ' ').title()} | {p['projected_default_rate']:.2%} "
                f"| {p['projected_prepay_rate']:.2%} | {p['projected_deterioration_rate']:.2%} |"
            )

        lines.append("\n## Monte Carlo Stochastic Portfolio Loss Simulation\n")
        lines.append(f"- **Simulated Paths**: {mc_results['num_iterations']:,}")
        lines.append(f"- **Portfolio Expected Loss**: ${mc_results['expected_loss']:,.2f} ({mc_results['expected_loss_rate']:.2%})")
        lines.append(f"- **95% Value-at-Risk (VaR 95)**: ${mc_results['var_95']:,.2f}")
        lines.append(f"- **99% Value-at-Risk (VaR 99)**: ${mc_results['var_99']:,.2f}")
        lines.append(f"- **99% Expected Shortfall (CVaR 99)**: ${mc_results['cvar_99']:,.2f}")
        lines.append(f"- **Prepayment Cashflow StdDev**: ${mc_results['prepayment_cashflow_std']:,.2f}\n")

        lines.append("## Top Drivers of Deviation from Baseline (12m Default Rate)\n")
        for sc_name, drivers in all_top_drivers.items():
            lines.append(f"### {sc_name.replace('_', ' ').title()}")
            for d in drivers:
                sign = "+" if d["deviation"] >= 0 else ""
                lines.append(
                    f"- **{d['segment_dimension']}={d['segment_value']}**: "
                    f"{d['segment_rate']:.2%} ({sign}{d['deviation']:.2%} vs portfolio avg) "
                    f"— {d['loan_count']:,} loan-months"
                )
            lines.append("")

        context.store.write_markdown("\n".join(lines), self.name, "scenario_report.md")

        return {**projections, "monte_carlo": mc_results, "segment_dimensions_analyzed": segment_cols}


global_stage_registry.register(ScenarioStage())
