"""Centralized SmartSeg business segmentation rules.

This module is the single source of truth for post-clustering business segment
names. K-Means/Hierarchical/DBSCAN still decide cluster membership; this layer
profiles each raw cluster and assigns business names from metrics only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd


BROAD_SEGMENTS = {
    "At Risk Customers",
    "Premium Customers",
    "High Value Customers",
    "Medium Value Customers",
    "Low Value Customers",
}

DETAILED_SEGMENTS = {
    "At Risk Customers",
    "International Customers",
    "Data Driven Customers",
    "Premium Customers",
    "High Value Customers",
    "Growth Potential Customers",
    "Medium Value Customers",
    "Low Value Customers",
}

SEGMENTATION_RULE_VERSION = "business-v5-revenue-weighted-value"
NAMING_SOURCE = "backend/business_segmentation.py"

VALUE_SEGMENT_ORDER = (
    "Premium Customers",
    "High Value Customers",
    "Medium Value Customers",
    "Low Value Customers",
)


@dataclass(frozen=True)
class MetricSpec:
    output_name: str
    aliases: tuple[str, ...]
    default: float


METRIC_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec(
        "arpu",
        (
            "arpu",
            "avg_arpu",
            "monthly_arpu",
            "monthly_arpu_dt",
            "monthly_arpu_tnd",
            "monthly_spend",
            "monthly_spend_tnd",
            "monthly_bill",
            "monthly_bill_dinar",
            "monthly_charges",
            "revenue",
        ),
        0.0,
    ),
    MetricSpec(
        "data_usage",
        (
            "data_usage",
            "avg_data_usage",
            "data_consumption_gb",
            "monthly_data_gb",
            "data_gb_monthly",
            "avg_data_gb",
            "internet_usage",
            "data_gb",
        ),
        0.0,
    ),
    MetricSpec(
        "voice_minutes",
        (
            "voice_minutes",
            "avg_voice_minutes",
            "voice_minutes_monthly",
            "monthly_calls_min",
            "call_minutes",
            "calls_minutes",
            "minutes",
        ),
        0.0,
    ),
    MetricSpec(
        "international_minutes",
        (
            "international_minutes",
            "avg_international_minutes",
            "international_calls_min",
            "international_min",
            "intl_minutes",
            "intl_min",
        ),
        0.0,
    ),
    MetricSpec(
        "clv",
        (
            "clv",
            "avg_clv",
            "customer_lifetime_value",
            "lifetime_value",
            "customer_value",
        ),
        0.0,
    ),
    MetricSpec(
        "satisfaction",
        (
            "satisfaction",
            "avg_satisfaction",
            "satisfaction_score",
            "customer_satisfaction",
            "csat",
            "nps",
        ),
        7.0,
    ),
    MetricSpec(
        "complaints",
        (
            "complaints",
            "avg_complaints",
            "complaint_count",
            "complaints_count",
            "support_tickets",
            "tickets",
        ),
        0.0,
    ),
    MetricSpec(
        "late_payments",
        (
            "late_payments",
            "avg_late_payments",
            "late_payment_count",
            "overdue_payments",
            "payment_delays",
            "delinquency",
        ),
        0.0,
    ),
    MetricSpec(
        "tenure_months",
        (
            "tenure_months",
            "avg_tenure_months",
            "account_tenure_months",
            "customer_tenure_months",
            "customer_tenure",
            "tenure",
            "months_active",
            "subscription_age",
        ),
        0.0,
    ),
    MetricSpec(
        "churn_probability",
        (
            "churn_probability",
            "avg_churn_probability",
            "churn_risk_score",
            "churn_risk",
            "churn_prob",
            "churn_score",
            "churn",
        ),
        0.0,
    ),
)


class BusinessSegmentationService:
    """Assign and aggregate business segment names from cluster metrics."""

    def segment_clusters(
        self,
        data: pd.DataFrame,
        labels: Iterable[int],
        mode_cluster_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        labels_array = np.asarray(list(labels))
        metric_frame = self.build_metric_frame(data)
        unique_cluster_ids = [int(value) for value in sorted(set(labels_array)) if int(value) != -1]
        k_for_mode = int(mode_cluster_count or len(unique_cluster_ids))

        raw_profiles = [
            self._build_cluster_profile(cluster_id, labels_array, metric_frame)
            for cluster_id in unique_cluster_ids
        ]
        self._apply_cluster_scores(raw_profiles)
        high_clv_threshold = self._high_clv_threshold(raw_profiles)
        risk_context = self._build_risk_context(raw_profiles)
        assignment_context = self._build_assignment_context(raw_profiles)
        if k_for_mode in {2, 3, 4, 5} and len(raw_profiles) == k_for_mode:
            assignment_context["stable_ranked_mode"] = 1.0
        stable_ranked_segments = self._assign_stable_ranked_segments(
            raw_profiles,
            k_for_mode,
            high_clv_threshold,
            risk_context,
            assignment_context,
        )

        segment_by_cluster = self._assign_initial_segments(
            raw_profiles,
            k_for_mode,
            high_clv_threshold,
            risk_context,
            assignment_context,
            stable_ranked_segments,
        )
        self._enforce_value_label_consistency(raw_profiles, segment_by_cluster)

        clusters: List[Dict[str, Any]] = []
        warnings: List[str] = []
        validation: Dict[str, Any] = {"clusters": {}, "business_segments": {}}
        for profile in raw_profiles:
            segment_name = segment_by_cluster[int(profile["cluster_id"])]
            assignment_mode = "ranked" if stable_ranked_segments is not None else (
                "detailed" if k_for_mode > 5 else "broad"
            )
            validation_messages = self._validate_profile(
                profile,
                segment_name,
                high_clv_threshold,
                risk_context,
                assignment_context,
            )
            cluster = {
                **profile,
                "size": profile["customer_count"],
                "percentage": self._percentage(profile["customer_count"], len(labels_array)),
                "business_segment": segment_name,
                "rule_version": SEGMENTATION_RULE_VERSION,
                "naming_source": NAMING_SOURCE,
                "validation_warnings": validation_messages,
                "assignment_mode": assignment_mode,
            }
            clusters.append(cluster)
            validation["clusters"][str(profile["cluster_id"])] = validation_messages

        business_segments = self._aggregate_business_segments(clusters, len(labels_array))
        for segment in business_segments:
            validation["business_segments"][segment["business_segment"]] = segment["validation_warnings"]

        at_risk_customers = sum(
            segment["customer_count"]
            for segment in business_segments
            if segment["business_segment"] == "At Risk Customers"
        )
        if len(labels_array) > 0 and at_risk_customers == len(labels_array):
            warnings.append(
                "All customers were classified as At Risk. Re-check risk thresholds or input risk metrics."
            )

        return {
            "segmentation_rule_version": SEGMENTATION_RULE_VERSION,
            "rule_version": SEGMENTATION_RULE_VERSION,
            "naming_source": NAMING_SOURCE,
            "clusters": clusters,
            "business_segments": business_segments,
            "warnings": warnings,
            "validation": validation,
            "cluster_segment_map": segment_by_cluster,
        }

    def build_metric_frame(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return normalized customer metrics used by exports and profiles.

        Missing optional metrics use neutral defaults so an uploaded dataset is
        still clusterable when it lacks, for example, complaints or late-payment
        columns. CLV is safely derived from ARPU * tenure when no explicit CLV
        column exists; otherwise it defaults to 0.
        """
        frame = pd.DataFrame(index=data.index)
        source_columns: Dict[str, Optional[str]] = {}

        for spec in METRIC_SPECS:
            column = self._find_column(data, spec.aliases)
            source_columns[spec.output_name] = column
            if column is None:
                frame[spec.output_name] = spec.default
            else:
                frame[spec.output_name] = pd.to_numeric(data[column], errors="coerce").fillna(spec.default)

        frame["tenure_months"] = self._normalize_tenure_months(
            frame["tenure_months"],
            source_columns.get("tenure_months"),
        )
        frame["churn_probability"] = self._normalize_percent(frame["churn_probability"])
        frame["satisfaction"] = self._normalize_satisfaction(frame["satisfaction"])

        if source_columns.get("clv") is None and (
            source_columns.get("arpu") is not None or source_columns.get("tenure_months") is not None
        ):
            frame["clv"] = frame["arpu"] * frame["tenure_months"]

        return frame

    def enrich_customer_dataframe(
        self,
        data: pd.DataFrame,
        labels: Iterable[int],
        segmentation: Dict[str, Any],
    ) -> pd.DataFrame:
        enriched = data.copy()
        labels_array = np.asarray(list(labels))
        cluster_map = segmentation.get("cluster_segment_map", {})
        metric_frame = self.build_metric_frame(data)

        enriched["cluster_id"] = labels_array
        enriched["cluster"] = labels_array
        enriched["business_segment"] = [
            cluster_map.get(int(cluster_id), "Low Value Customers")
            for cluster_id in labels_array
        ]
        enriched["tenure_months"] = metric_frame["tenure_months"].round(3)
        enriched["arpu_tnd"] = metric_frame["arpu"].round(3)
        enriched["arpu_dt"] = metric_frame["arpu"].round(3)
        enriched["data_usage"] = metric_frame["data_usage"].round(3)
        enriched["voice_minutes"] = metric_frame["voice_minutes"].round(3)
        enriched["international_minutes"] = metric_frame["international_minutes"].round(3)
        enriched["clv"] = metric_frame["clv"].round(3)
        enriched["satisfaction"] = metric_frame["satisfaction"].round(3)
        enriched["complaints"] = metric_frame["complaints"].round(3)
        enriched["late_payments"] = metric_frame["late_payments"].round(3)
        enriched["churn_probability"] = metric_frame["churn_probability"].round(3)

        return enriched

    def _build_cluster_profile(
        self,
        cluster_id: int,
        labels: np.ndarray,
        metric_frame: pd.DataFrame,
    ) -> Dict[str, Any]:
        mask = labels == cluster_id
        cluster_metrics = metric_frame.loc[mask]

        return {
            "cluster_id": int(cluster_id),
            "customer_count": int(mask.sum()),
            "avg_arpu": self._round(cluster_metrics["arpu"].mean()),
            "avg_data_usage": self._round(cluster_metrics["data_usage"].mean()),
            "avg_voice_minutes": self._round(cluster_metrics["voice_minutes"].mean()),
            "avg_international_minutes": self._round(cluster_metrics["international_minutes"].mean()),
            "avg_clv": self._round(cluster_metrics["clv"].mean()),
            "avg_satisfaction": self._round(cluster_metrics["satisfaction"].mean()),
            "avg_complaints": self._round(cluster_metrics["complaints"].mean()),
            "avg_late_payments": self._round(cluster_metrics["late_payments"].mean()),
            "avg_tenure_months": self._round(cluster_metrics["tenure_months"].mean()),
            "avg_churn_probability": self._round(cluster_metrics["churn_probability"].mean()),
        }

    def _apply_cluster_scores(self, profiles: List[Dict[str, Any]]) -> None:
        """Add relative value/risk scores used for K=2..5 interpretation."""
        if not profiles:
            return

        normalized = {
            "arpu": self._normalized_values(profiles, "avg_arpu"),
            "data_usage": self._normalized_values(profiles, "avg_data_usage"),
            "voice_minutes": self._normalized_values(profiles, "avg_voice_minutes"),
            "clv": self._normalized_values(profiles, "avg_clv"),
            "tenure_months": self._normalized_values(profiles, "avg_tenure_months"),
            "churn_probability": self._normalized_values(profiles, "avg_churn_probability"),
            "complaints": self._normalized_values(profiles, "avg_complaints"),
            "late_payments": self._normalized_values(profiles, "avg_late_payments"),
            "satisfaction": self._normalized_values(profiles, "avg_satisfaction"),
        }

        for index, profile in enumerate(profiles):
            value_score = (
                normalized["arpu"][index] * 0.50
                + normalized["clv"][index] * 0.25
                + normalized["data_usage"][index] * 0.15
                + normalized["tenure_months"][index] * 0.05
                + normalized["voice_minutes"][index] * 0.05
            )
            risk_components = [
                normalized["churn_probability"][index],
                normalized["complaints"][index],
                normalized["late_payments"][index],
                1 - normalized["satisfaction"][index],
                1 - normalized["arpu"][index],
                1 - normalized["data_usage"][index],
                1 - normalized["voice_minutes"][index],
            ]
            profile["value_score"] = self._round(float(value_score), 4)
            profile["risk_score"] = self._round(float(np.mean(risk_components)), 4)

        for rank, profile in enumerate(self._sort_by_value(profiles), start=1):
            profile["value_rank"] = rank
        for rank, profile in enumerate(self._sort_by_risk(profiles), start=1):
            profile["risk_rank"] = rank

    def _assign_initial_segments(
        self,
        profiles: List[Dict[str, Any]],
        k_for_mode: int,
        high_clv_threshold: float,
        risk_context: Dict[str, float],
        assignment_context: Dict[str, float],
        stable_ranked_segments: Optional[Dict[int, str]],
    ) -> Dict[int, str]:
        if stable_ranked_segments is not None:
            return dict(stable_ranked_segments)

        return {
            int(profile["cluster_id"]): self._assign_business_segment(
                profile,
                k_for_mode,
                high_clv_threshold,
                risk_context,
                assignment_context,
            )
            for profile in profiles
        }

    def _enforce_value_label_consistency(
        self,
        profiles: List[Dict[str, Any]],
        segment_by_cluster: Dict[int, str],
    ) -> None:
        """Keep value labels ordered by business value after initial naming.

        At Risk is intentionally not touched here because it describes churn
        behavior, not spending value.
        """
        profiles_by_id = {int(profile["cluster_id"]): profile for profile in profiles}
        value_profiles = [
            profiles_by_id[cluster_id]
            for cluster_id, segment_name in segment_by_cluster.items()
            if segment_name in VALUE_SEGMENT_ORDER
        ]
        if len(value_profiles) < 2:
            return

        current_labels = [
            segment_by_cluster[int(profile["cluster_id"])]
            for profile in value_profiles
        ]
        ordered_labels = sorted(
            current_labels,
            key=lambda segment_name: VALUE_SEGMENT_ORDER.index(segment_name),
        )
        ordered_profiles = self._sort_by_value(value_profiles)

        for profile, segment_name in zip(ordered_profiles, ordered_labels):
            segment_by_cluster[int(profile["cluster_id"])] = segment_name

        self._swap_medium_low_by_value_score(profiles, segment_by_cluster)
        self._swap_low_medium_when_low_is_stronger(profiles, segment_by_cluster)

    def _swap_low_medium_when_low_is_stronger(
        self,
        profiles: List[Dict[str, Any]],
        segment_by_cluster: Dict[int, str],
    ) -> None:
        profiles_by_id = {int(profile["cluster_id"]): profile for profile in profiles}
        low_profiles = [
            profiles_by_id[cluster_id]
            for cluster_id, segment_name in segment_by_cluster.items()
            if segment_name == "Low Value Customers"
        ]
        medium_profiles = [
            profiles_by_id[cluster_id]
            for cluster_id, segment_name in segment_by_cluster.items()
            if segment_name == "Medium Value Customers"
        ]

        for low_profile in low_profiles:
            for medium_profile in medium_profiles:
                if self._low_value_is_stronger_than_medium(low_profile, medium_profile):
                    segment_by_cluster[int(low_profile["cluster_id"])] = "Medium Value Customers"
                    segment_by_cluster[int(medium_profile["cluster_id"])] = "Low Value Customers"

    def _low_value_is_stronger_than_medium(
        self,
        low_profile: Dict[str, Any],
        medium_profile: Dict[str, Any],
    ) -> bool:
        return (
            low_profile["avg_arpu"] > medium_profile["avg_arpu"]
            and low_profile["avg_data_usage"] > medium_profile["avg_data_usage"]
        )

    def _swap_medium_low_by_value_score(
        self,
        profiles: List[Dict[str, Any]],
        segment_by_cluster: Dict[int, str],
    ) -> None:
        profiles_by_id = {int(profile["cluster_id"]): profile for profile in profiles}
        low_profiles = [
            profiles_by_id[cluster_id]
            for cluster_id, segment_name in segment_by_cluster.items()
            if segment_name == "Low Value Customers"
        ]
        medium_profiles = [
            profiles_by_id[cluster_id]
            for cluster_id, segment_name in segment_by_cluster.items()
            if segment_name == "Medium Value Customers"
        ]

        for low_profile in low_profiles:
            for medium_profile in medium_profiles:
                if low_profile.get("value_score", 0) > medium_profile.get("value_score", 0):
                    segment_by_cluster[int(low_profile["cluster_id"])] = "Medium Value Customers"
                    segment_by_cluster[int(medium_profile["cluster_id"])] = "Low Value Customers"

    def _normalized_values(self, profiles: List[Dict[str, Any]], metric: str) -> List[float]:
        values = [float(profile[metric]) for profile in profiles]
        low = min(values)
        high = max(values)
        if high == low:
            return [0.5 for _ in values]
        return [(value - low) / (high - low) for value in values]

    def _assign_stable_ranked_segments(
        self,
        profiles: List[Dict[str, Any]],
        k_for_mode: int,
        high_clv_threshold: float,
        risk_context: Dict[str, float],
        assignment_context: Dict[str, float],
    ) -> Optional[Dict[int, str]]:
        """Return unique broad business names for K=2..5.

        This layer interprets the mathematical clusters by relative score, not
        by cluster id and not by rigid absolute thresholds.
        """
        if k_for_mode not in {2, 3, 4, 5} or len(profiles) != k_for_mode:
            return None

        by_value = self._sort_by_value(profiles)
        by_risk = self._sort_by_risk(profiles)
        risk_profile = by_risk[0]
        has_clear_risk = self._has_clearly_risky_cluster(profiles, risk_profile, risk_context)

        if k_for_mode == 2:
            if has_clear_risk:
                remaining = [profile for profile in profiles if profile is not risk_profile][0]
                remaining_name = (
                    "High Value Customers"
                    if self._has_strong_value(remaining, high_clv_threshold, assignment_context)
                    else "Low Value Customers"
                )
                return {
                    int(risk_profile["cluster_id"]): "At Risk Customers",
                    int(remaining["cluster_id"]): remaining_name,
                }

            return {
                int(by_value[0]["cluster_id"]): "High Value Customers",
                int(by_value[-1]["cluster_id"]): "Low Value Customers",
            }

        if k_for_mode == 3:
            if has_clear_risk:
                remaining = self._sort_by_value([profile for profile in profiles if profile is not risk_profile])
                return {
                    int(risk_profile["cluster_id"]): "At Risk Customers",
                    int(remaining[0]["cluster_id"]): "High Value Customers",
                    int(remaining[-1]["cluster_id"]): "Low Value Customers",
                }

            return {
                int(by_value[0]["cluster_id"]): "Premium Customers",
                int(by_value[1]["cluster_id"]): "Medium Value Customers",
                int(by_value[-1]["cluster_id"]): "Low Value Customers",
            }

        if k_for_mode == 4:
            if has_clear_risk:
                remaining = self._sort_by_value([profile for profile in profiles if profile is not risk_profile])
                return {
                    int(risk_profile["cluster_id"]): "At Risk Customers",
                    int(remaining[0]["cluster_id"]): "Premium Customers",
                    int(remaining[1]["cluster_id"]): "High Value Customers",
                    int(remaining[-1]["cluster_id"]): "Low Value Customers",
                }

            return {
                int(by_value[0]["cluster_id"]): "Premium Customers",
                int(by_value[1]["cluster_id"]): "High Value Customers",
                int(by_value[2]["cluster_id"]): "Medium Value Customers",
                int(by_value[-1]["cluster_id"]): "Low Value Customers",
            }

        remaining = self._sort_by_value([profile for profile in profiles if profile is not risk_profile])
        return {
            int(risk_profile["cluster_id"]): "At Risk Customers",
            int(remaining[0]["cluster_id"]): "Premium Customers",
            int(remaining[1]["cluster_id"]): "High Value Customers",
            int(remaining[-1]["cluster_id"]): "Low Value Customers",
            int(remaining[2]["cluster_id"]): "Medium Value Customers",
        }

    def _sort_by_value(self, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            profiles,
            key=lambda profile: (
                -profile.get("value_score", 0),
                -profile["avg_arpu"],
                -profile["avg_clv"],
                -profile["avg_data_usage"],
                -profile["avg_tenure_months"],
                -profile["customer_count"],
                profile["cluster_id"],
            ),
        )

    def _sort_by_risk(self, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            profiles,
            key=lambda profile: (
                -profile.get("risk_score", 0),
                -profile["avg_churn_probability"],
                -profile["avg_complaints"],
                -profile["avg_late_payments"],
                profile["avg_satisfaction"],
                profile["cluster_id"],
            ),
        )

    def _has_clearly_risky_cluster(
        self,
        profiles: List[Dict[str, Any]],
        risk_profile: Dict[str, Any],
        risk_context: Dict[str, float],
    ) -> bool:
        risk_scores = [float(profile.get("risk_score", 0)) for profile in profiles]
        median_risk = float(np.median(risk_scores))
        meaningfully_higher = risk_profile.get("risk_score", 0) >= median_risk + 0.15
        return meaningfully_higher or self._is_at_risk(risk_profile, risk_context)

    def _has_strong_value(
        self,
        profile: Dict[str, Any],
        high_clv_threshold: float,
        assignment_context: Dict[str, float],
    ) -> bool:
        return (
            profile.get("value_score", 0) >= 0.6
            or profile["avg_arpu"] >= 70
            or self._is_high_clv(profile, high_clv_threshold)
            or (
                profile["avg_arpu"] >= assignment_context["arpu_p50"]
                and profile["avg_data_usage"] >= assignment_context["data_p50"]
            )
        )

    def _assign_business_segment(
        self,
        profile: Dict[str, Any],
        k_for_mode: int,
        high_clv_threshold: float,
        risk_context: Dict[str, float],
        assignment_context: Dict[str, float],
    ) -> str:
        if k_for_mode <= 5:
            rules = (
                ("At Risk Customers", self._is_at_risk(profile, risk_context)),
                ("Premium Customers", self._is_premium(profile)),
                ("High Value Customers", self._is_broad_high_value(profile, high_clv_threshold)),
                ("Medium Value Customers", self._is_broad_medium_value(profile)),
                ("Low Value Customers", True),
            )
        else:
            rules = (
                ("At Risk Customers", self._is_at_risk(profile, risk_context)),
                ("International Customers", self._is_international(profile)),
                ("Data Driven Customers", self._is_data_driven(profile)),
                ("Premium Customers", self._is_premium(profile)),
                (
                    "High Value Customers",
                    self._is_detailed_high_value(profile)
                    or self._is_adaptive_high_value(profile, assignment_context, high_clv_threshold),
                ),
                (
                    "Growth Potential Customers",
                    self._is_growth_potential(profile)
                    or self._is_adaptive_growth_potential(profile, assignment_context),
                ),
                (
                    "Medium Value Customers",
                    self._is_detailed_medium_value(profile)
                    or self._is_adaptive_medium_value(profile, assignment_context),
                ),
                ("Low Value Customers", True),
            )

        for segment_name, matches in rules:
            if matches and not self._validate_profile(
                profile,
                segment_name,
                high_clv_threshold,
                risk_context,
                assignment_context,
            ):
                return segment_name

        return "Low Value Customers"

    def _aggregate_business_segments(
        self,
        clusters: List[Dict[str, Any]],
        total_customers: int,
    ) -> List[Dict[str, Any]]:
        by_segment: Dict[str, List[Dict[str, Any]]] = {}
        for cluster in clusters:
            by_segment.setdefault(cluster["business_segment"], []).append(cluster)

        order = [
            "At Risk Customers",
            "International Customers",
            "Data Driven Customers",
            "Premium Customers",
            "High Value Customers",
            "Growth Potential Customers",
            "Medium Value Customers",
            "Low Value Customers",
        ]
        segments = []
        for segment_name in order:
            items = by_segment.get(segment_name)
            if not items:
                continue

            customer_count = sum(item["customer_count"] for item in items)
            aggregated = {
                "business_segment": segment_name,
                "name": segment_name,
                "cluster_id": None,
                "customer_count": int(customer_count),
                "percentage": self._percentage(customer_count, total_customers),
                "source_cluster_ids": [int(item["cluster_id"]) for item in items],
                "rule_version": SEGMENTATION_RULE_VERSION,
                "naming_source": NAMING_SOURCE,
                "value_score": self._weighted_average(items, "value_score"),
                "risk_score": self._weighted_average(items, "risk_score"),
                "avg_arpu": self._weighted_average(items, "avg_arpu"),
                "avg_data_usage": self._weighted_average(items, "avg_data_usage"),
                "avg_voice_minutes": self._weighted_average(items, "avg_voice_minutes"),
                "avg_international_minutes": self._weighted_average(items, "avg_international_minutes"),
                "avg_clv": self._weighted_average(items, "avg_clv"),
                "avg_satisfaction": self._weighted_average(items, "avg_satisfaction"),
                "avg_complaints": self._weighted_average(items, "avg_complaints"),
                "avg_late_payments": self._weighted_average(items, "avg_late_payments"),
                "avg_tenure_months": self._weighted_average(items, "avg_tenure_months"),
                "avg_churn_probability": self._weighted_average(items, "avg_churn_probability"),
                "validation_warnings": sorted(
                    set(
                        warning
                        for item in items
                        for warning in item.get("validation_warnings", [])
                    )
                ),
            }
            segments.append(aggregated)

        return segments

    def _validate_profile(
        self,
        profile: Dict[str, Any],
        segment_name: str,
        high_clv_threshold: float,
        risk_context: Optional[Dict[str, float]] = None,
        assignment_context: Optional[Dict[str, float]] = None,
    ) -> List[str]:
        warnings: List[str] = []
        risk_context = risk_context or {"late_payments_threshold": 5.0, "complaints_threshold": 3.0}
        assignment_context = assignment_context or self._empty_assignment_context()
        ranked_mode = bool(assignment_context.get("stable_ranked_mode"))

        ranked_at_risk_valid = ranked_mode and profile.get("risk_rank") == 1
        ranked_premium_valid = ranked_mode and profile.get("value_rank") == 1
        ranked_high_value_valid = ranked_mode and profile.get("value_rank") in {1, 2}
        ranked_medium_value_valid = ranked_mode and profile.get("value_rank") not in {
            1,
            assignment_context.get("cluster_count"),
        }
        ranked_low_value_valid = ranked_mode and profile.get("value_rank") == assignment_context.get("cluster_count")

        if segment_name == "At Risk Customers" and not (
            self._is_at_risk(profile, risk_context) or ranked_at_risk_valid
        ):
            warnings.append("At Risk Customers requires strong churn, satisfaction, complaint, payment, or inactivity evidence.")
        if segment_name == "Premium Customers" and not self._is_premium(profile):
            if not ranked_premium_valid:
                warnings.append("Premium average ARPU must be >= 150 DT and data usage >= 100.")
        high_value_valid = (
            profile["avg_arpu"] >= 70
            or self._is_high_clv(profile, high_clv_threshold)
            or self._is_adaptive_high_value(profile, assignment_context, high_clv_threshold)
            or ranked_high_value_valid
        )
        if segment_name == "High Value Customers" and not high_value_valid:
            warnings.append("High Value average ARPU must satisfy the active broad or detailed ARPU rule unless justified by high CLV.")
        medium_value_valid = (
            self._broad_medium_value_supported(profile)
            or self._is_detailed_medium_value(profile)
            or self._is_adaptive_medium_value(profile, assignment_context)
            or ranked_medium_value_valid
        )
        if segment_name == "Medium Value Customers" and not medium_value_valid:
            warnings.append("Medium Value average ARPU must fit the active broad or detailed ARPU/usage rule.")
        if segment_name == "Low Value Customers" and not (
            profile["avg_arpu"] < 25 or self._has_low_usage(profile) or ranked_low_value_valid
        ):
            warnings.append("Low Value average ARPU should be below 25 DT unless it is fallback due to very low usage.")
        if segment_name == "International Customers" and not self._is_international(profile):
            warnings.append("International Customers must have avg_international_minutes >= 150 and ARPU >= 50 DT.")
        if segment_name == "Data Driven Customers" and not self._is_data_driven(profile):
            warnings.append("Data Driven Customers must have avg_data_usage >= 250, voice < 400, and ARPU >= 40 DT.")
        growth_valid = (
            self._is_growth_potential(profile)
            or self._is_adaptive_growth_potential(profile, assignment_context)
        )
        if segment_name == "Growth Potential Customers" and not growth_valid:
            warnings.append("Growth Potential requires ARPU 45-90 DT, data usage >= 60, satisfaction >= 6, and churn probability < 60.")

        return warnings

    def _is_at_risk(self, profile: Dict[str, Any], risk_context: Dict[str, float]) -> bool:
        severe_inactivity = (
            profile["avg_arpu"] < 5
            and profile["avg_data_usage"] < 1
            and profile["avg_voice_minutes"] < 10
        )
        high_complaints = profile["avg_complaints"] >= risk_context["complaints_threshold"]
        high_late_payments = profile["avg_late_payments"] >= risk_context["late_payments_threshold"]

        return (
            profile["avg_churn_probability"] >= 70
            or profile["avg_satisfaction"] <= 4
            or high_complaints
            or high_late_payments
            or severe_inactivity
        )

    def _is_premium(self, profile: Dict[str, Any]) -> bool:
        return profile["avg_arpu"] >= 150 and profile["avg_data_usage"] >= 100

    def _is_broad_high_value(self, profile: Dict[str, Any], high_clv_threshold: float) -> bool:
        return profile["avg_arpu"] >= 70 or self._is_high_clv(profile, high_clv_threshold)

    def _is_detailed_high_value(self, profile: Dict[str, Any]) -> bool:
        return profile["avg_arpu"] >= 90 and profile["avg_arpu"] < 150

    def _broad_medium_value_supported(self, profile: Dict[str, Any]) -> bool:
        return profile["avg_arpu"] >= 20 and profile["avg_arpu"] < 70

    def _is_broad_medium_value(self, profile: Dict[str, Any]) -> bool:
        return self._broad_medium_value_supported(profile)

    def _is_detailed_medium_value(self, profile: Dict[str, Any]) -> bool:
        return (
            profile["avg_arpu"] >= 25
            and profile["avg_arpu"] < 45
            and self._has_normal_data_usage(profile)
            and not self._is_international(profile)
            and not self._is_data_driven(profile)
        )

    def _is_international(self, profile: Dict[str, Any]) -> bool:
        return profile["avg_international_minutes"] >= 150 and profile["avg_arpu"] >= 50

    def _is_data_driven(self, profile: Dict[str, Any]) -> bool:
        return (
            profile["avg_data_usage"] >= 250
            and profile["avg_voice_minutes"] < 400
            and profile["avg_arpu"] >= 40
        )

    def _is_growth_potential(self, profile: Dict[str, Any]) -> bool:
        return (
            profile["avg_arpu"] >= 45
            and profile["avg_arpu"] < 90
            and profile["avg_data_usage"] >= 60
            and profile["avg_churn_probability"] < 60
            and profile["avg_satisfaction"] >= 6
        )

    def _is_high_clv(self, profile: Dict[str, Any], high_clv_threshold: float) -> bool:
        return high_clv_threshold > 0 and profile["avg_clv"] >= high_clv_threshold

    def _is_adaptive_high_value(
        self,
        profile: Dict[str, Any],
        assignment_context: Dict[str, float],
        high_clv_threshold: float,
    ) -> bool:
        if not assignment_context["adaptive_value_tiers"]:
            return False

        return (
            profile["avg_arpu"] >= assignment_context["arpu_p80"]
            and self._is_high_clv(profile, high_clv_threshold)
        )

    def _is_adaptive_growth_potential(
        self,
        profile: Dict[str, Any],
        assignment_context: Dict[str, float],
    ) -> bool:
        if not assignment_context["adaptive_value_tiers"]:
            return False

        return (
            profile["avg_arpu"] >= assignment_context["arpu_p50"]
            and profile["avg_arpu"] < assignment_context["arpu_p80"]
            and profile["avg_data_usage"] >= assignment_context["data_p50"]
            and profile["avg_churn_probability"] < 60
            and profile["avg_satisfaction"] >= 6
        )

    def _is_adaptive_medium_value(
        self,
        profile: Dict[str, Any],
        assignment_context: Dict[str, float],
    ) -> bool:
        if not assignment_context["adaptive_value_tiers"]:
            return False

        return (
            profile["avg_arpu"] >= assignment_context["arpu_p25"]
            and profile["avg_arpu"] < assignment_context["arpu_p50"]
            and self._has_normal_data_usage(profile)
            and not self._is_international(profile)
            and not self._is_data_driven(profile)
        )

    def _has_low_usage(self, profile: Dict[str, Any]) -> bool:
        return profile["avg_data_usage"] < 1 and profile["avg_voice_minutes"] < 10

    def _has_normal_data_usage(self, profile: Dict[str, Any]) -> bool:
        return profile["avg_data_usage"] < 250

    def _high_clv_threshold(self, profiles: List[Dict[str, Any]]) -> float:
        clv_values = [profile["avg_clv"] for profile in profiles if profile["avg_clv"] > 0]
        if not clv_values:
            return 0.0
        return float(np.percentile(clv_values, 75))

    def _empty_assignment_context(self) -> Dict[str, float]:
        return {
            "adaptive_value_tiers": 0.0,
            "stable_ranked_mode": 0.0,
            "cluster_count": 0.0,
            "arpu_p25": 25.0,
            "arpu_p50": 45.0,
            "arpu_p80": 90.0,
            "data_p50": 60.0,
        }

    def _build_assignment_context(self, profiles: List[Dict[str, Any]]) -> Dict[str, float]:
        if not profiles:
            return self._empty_assignment_context()

        arpu_values = [profile["avg_arpu"] for profile in profiles]
        data_values = [profile["avg_data_usage"] for profile in profiles]

        context = {
            "adaptive_value_tiers": 0.0,
            "stable_ranked_mode": 0.0,
            "cluster_count": float(len(profiles)),
            "arpu_p25": float(np.percentile(arpu_values, 25)),
            "arpu_p50": float(np.percentile(arpu_values, 50)),
            "arpu_p80": float(np.percentile(arpu_values, 80)),
            "data_p50": float(np.percentile(data_values, 50)),
        }

        # Some demo/preprocessed telecom datasets store ARPU on a compressed
        # numeric scale even when the column name says TND/DT. In detailed mode,
        # absolute Premium/International/Data rules still win first, but ordinary
        # value tiers may use cluster percentiles so K=6/7/8 does not collapse
        # into a single Low/Medium card because of units alone.
        context["adaptive_value_tiers"] = 1.0 if float(np.percentile(arpu_values, 90)) < 70 else 0.0
        return context

    def _build_risk_context(self, profiles: List[Dict[str, Any]]) -> Dict[str, float]:
        """Guard optional risk metrics from dominating every cluster.

        The business threshold remains complaints >= 3 and late payments >= 5.
        When most clusters exceed one of those thresholds, that metric is not
        discriminative for naming and must be an upper-decile outlier before it
        can force At Risk on otherwise healthy, active clusters.
        """
        if not profiles:
            return {"complaints_threshold": 3.0, "late_payments_threshold": 5.0}

        complaint_values = [profile["avg_complaints"] for profile in profiles]
        late_payment_values = [profile["avg_late_payments"] for profile in profiles]
        complaint_rate = sum(value >= 3 for value in complaint_values) / len(complaint_values)
        late_payment_rate = sum(value >= 5 for value in late_payment_values) / len(late_payment_values)

        complaints_threshold = 3.0
        late_payments_threshold = 5.0

        if complaint_rate > 0.5:
            complaints_threshold = max(3.0, float(np.percentile(complaint_values, 90)))
        if late_payment_rate > 0.5:
            late_payments_threshold = max(5.0, float(np.percentile(late_payment_values, 90)))

        return {
            "complaints_threshold": complaints_threshold,
            "late_payments_threshold": late_payments_threshold,
        }

    def _find_column(self, data: pd.DataFrame, aliases: Iterable[str]) -> Optional[str]:
        normalized_columns = {self._normalize(column): column for column in data.columns}
        normalized_aliases = [self._normalize(alias) for alias in aliases]

        for alias in normalized_aliases:
            if alias in normalized_columns:
                return normalized_columns[alias]

        for column in data.columns:
            normalized_column = self._normalize(column)
            if any(alias in normalized_column for alias in normalized_aliases):
                return column

        return None

    def _normalize_tenure_months(self, values: pd.Series, column: Optional[str]) -> pd.Series:
        if column and "year" in self._normalize(column):
            return values * 12
        return values

    def _normalize_percent(self, values: pd.Series) -> pd.Series:
        normalized = values.apply(lambda value: value * 100 if value <= 1 else value)
        return normalized.clip(lower=0, upper=100)

    def _normalize_satisfaction(self, values: pd.Series) -> pd.Series:
        normalized = values.copy()
        normalized = np.where((normalized >= 0) & (normalized <= 1), normalized * 10, normalized)
        normalized = np.where((normalized > 1) & (normalized <= 5), normalized * 2, normalized)
        normalized = np.where(normalized > 10, normalized / 10, normalized)
        return pd.Series(normalized, index=values.index).clip(lower=0, upper=10)

    def _weighted_average(self, items: List[Dict[str, Any]], key: str) -> float:
        total = sum(item["customer_count"] for item in items)
        if total <= 0:
            return 0.0
        return self._round(sum(item[key] * item["customer_count"] for item in items) / total)

    def _percentage(self, value: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return self._round((value / total) * 100, digits=2)

    def _round(self, value: Any, digits: int = 3) -> float:
        if pd.isna(value):
            return 0.0
        return round(float(value), digits)

    def _normalize(self, value: str) -> str:
        return "".join(char.lower() if char.isalnum() else "_" for char in str(value)).strip("_")
