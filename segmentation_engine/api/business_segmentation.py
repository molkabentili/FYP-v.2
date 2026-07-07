"""Deterministic SmartSeg business interpretation layer.

K-Means creates mathematical clusters only. This module interprets those raw
clusters with a small rule-based telecom segment library. It does not train a
model, generate labels, use random conditions, or use natural-language logic for
assignment. Segment names always come from APPROVED_SEGMENTS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd


SEGMENTATION_RULE_VERSION = "business-v7-validated-adaptive-library"
NAMING_SOURCE = "backend/business_segmentation.py"

APPROVED_SEGMENTS = (
    "Premium Customers",
    "High Value Customers",
    "Medium Value Customers",
    "Low Value Customers",
    "At Risk Customers",
    "Growth Potential Customers",
    "Data Driven Customers",
    "Digital Enthusiast Customers",
    "International Customers",
    "Voice Focused Customers",
    "Loyal Customers",
    "New Customers",
    "Dormant Customers",
    "Budget Conscious Customers",
)

BROAD_SEGMENTS = {
    "At Risk Customers",
    "Premium Customers",
    "High Value Customers",
    "Medium Value Customers",
    "Low Value Customers",
}

DETAILED_SEGMENTS = set(APPROVED_SEGMENTS)

VALUE_SEGMENT_ORDER = (
    "Premium Customers",
    "High Value Customers",
    "Medium Value Customers",
    "Low Value Customers",
)

SPECIAL_SEGMENT_ORDER = (
    "At Risk Customers",
    "International Customers",
    "Data Driven Customers",
    "Digital Enthusiast Customers",
    "Voice Focused Customers",
    "Loyal Customers",
    "New Customers",
    "Dormant Customers",
    "Growth Potential Customers",
    "Budget Conscious Customers",
)


@dataclass(frozen=True)
class MetricSpec:
    output_name: str
    aliases: tuple[str, ...]
    default: float


@dataclass(frozen=True)
class SegmentDecision:
    name: str
    confidence: float
    explanation: str


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
    """Assign approved business segment names from cluster metrics only."""

    def segment_clusters(
        self,
        data: pd.DataFrame,
        labels: Iterable[int],
        mode_cluster_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        labels_array = np.asarray(list(labels))
        metric_frame = self.build_metric_frame(data)
        unique_cluster_ids = [int(value) for value in sorted(set(labels_array)) if int(value) != -1]

        profiles = [
            self._build_cluster_profile(cluster_id, labels_array, metric_frame)
            for cluster_id in unique_cluster_ids
        ]

        self._calculate_scores(profiles)
        decisions = self._assign_segments(profiles)
        self._validate_final_ordering(profiles, decisions)
        self._validate_final_assignments(profiles, decisions)

        clusters: List[Dict[str, Any]] = []
        warnings: List[str] = []
        validation: Dict[str, Any] = {"clusters": {}, "business_segments": {}}

        for profile in profiles:
            decision = decisions[int(profile["cluster_id"])]
            validation_messages = self._validate_assignment(profile, decision.name, profiles)
            cluster = {
                **profile,
                "size": profile["customer_count"],
                "percentage": self._percentage(profile["customer_count"], len(labels_array)),
                "business_segment": decision.name,
                "rule_version": SEGMENTATION_RULE_VERSION,
                "naming_source": NAMING_SOURCE,
                "naming_confidence": self._round(decision.confidence),
                "explanation": decision.explanation,
                "validation_warnings": validation_messages,
            }
            clusters.append(cluster)
            validation["clusters"][str(profile["cluster_id"])] = validation_messages

        business_segments = self._build_business_segment_cards(clusters, len(labels_array))
        for segment in business_segments:
            validation["business_segments"][str(segment["cluster_id"])] = segment["validation_warnings"]

        if clusters and all(cluster["business_segment"] == "At Risk Customers" for cluster in clusters):
            warnings.append(
                "All customers were classified as At Risk. Re-check risk thresholds or input risk metrics."
            )

        segment_by_cluster = {
            int(cluster["cluster_id"]): cluster["business_segment"]
            for cluster in clusters
        }

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
        """Return canonical customer metrics used by profiles and exports.

        Missing optional metrics use neutral defaults. CLV is safely derived from
        ARPU times tenure when no explicit CLV column exists; otherwise missing
        CLV remains neutral at 0 so uploads do not crash.
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

    def _calculate_scores(self, profiles: List[Dict[str, Any]]) -> None:
        if not profiles:
            return

        normalized = {
            "arpu": self._normalized_values(profiles, "avg_arpu"),
            "clv": self._normalized_values(profiles, "avg_clv"),
            "data": self._normalized_values(profiles, "avg_data_usage"),
            "voice": self._normalized_values(profiles, "avg_voice_minutes"),
            "international": self._normalized_values(profiles, "avg_international_minutes"),
            "tenure": self._normalized_values(profiles, "avg_tenure_months"),
            "satisfaction": self._normalized_values(profiles, "avg_satisfaction"),
            "complaints": self._normalized_values(profiles, "avg_complaints"),
            "late_payments": self._normalized_values(profiles, "avg_late_payments"),
            "churn": self._normalized_values(profiles, "avg_churn_probability"),
        }

        for index, profile in enumerate(profiles):
            arpu = normalized["arpu"][index]
            clv = normalized["clv"][index]
            data = normalized["data"][index]
            voice = normalized["voice"][index]
            international = normalized["international"][index]
            tenure = normalized["tenure"][index]
            satisfaction = normalized["satisfaction"][index]
            complaints = normalized["complaints"][index]
            late_payments = normalized["late_payments"][index]
            churn = normalized["churn"][index]
            inactivity = (1 - data + 1 - voice + 1 - arpu) / 3
            engagement = (data * 0.6) + (voice * 0.4)
            data_dominance = max(data - voice, 0.0)
            voice_dominance = max(voice - data, 0.0)
            medium_value_fit = max(0.0, 1.0 - abs(((arpu + clv) / 2) - 0.55) / 0.55)

            profile.update(
                {
                    "arpu_score": self._round(arpu, 4),
                    "clv_score": self._round(clv, 4),
                    "data_usage_score": self._round(data, 4),
                    "voice_usage_score": self._round(voice, 4),
                    "international_usage_score": self._round(international, 4),
                    "tenure_score": self._round(tenure, 4),
                    "satisfaction_score": self._round(satisfaction, 4),
                    "complaints_score": self._round(complaints, 4),
                    "late_payments_score": self._round(late_payments, 4),
                    "churn_score": self._round(churn, 4),
                    "value_score": self._round(
                        (arpu * 0.50) + (clv * 0.25) + (data * 0.15) + (tenure * 0.05) + (voice * 0.05),
                        4,
                    ),
                    "risk_score": self._round(
                        (churn * 0.35)
                        + ((1 - satisfaction) * 0.25)
                        + (complaints * 0.15)
                        + (late_payments * 0.15)
                        + (inactivity * 0.10),
                        4,
                    ),
                    "data_score": self._round((data * 0.75) + (data_dominance * 0.25), 4),
                    "international_score": self._round(international, 4),
                    "voice_score": self._round((voice * 0.70) + (voice_dominance * 0.30), 4),
                    "loyalty_score": self._round((tenure * 0.45) + (satisfaction * 0.35) + ((1 - churn) * 0.20), 4),
                    "growth_score": self._round(
                        (medium_value_fit * 0.35)
                        + (engagement * 0.30)
                        + (satisfaction * 0.20)
                        + ((1 - churn) * 0.15),
                        4,
                    ),
                    "digital_score": self._round((data * 0.50) + (((arpu + clv) / 2) * 0.35) + (engagement * 0.15), 4),
                    "dormant_score": self._round(inactivity, 4),
                    "budget_score": self._round(((1 - arpu) * 0.45) + (engagement * 0.35) + (satisfaction * 0.20), 4),
                }
            )

        for rank, profile in enumerate(self._sort_by(profiles, "value_score"), start=1):
            profile["value_rank"] = rank
        for rank, profile in enumerate(self._sort_by(profiles, "risk_score"), start=1):
            profile["risk_rank"] = rank

    def _assign_segments(self, profiles: List[Dict[str, Any]]) -> Dict[int, SegmentDecision]:
        decisions: Dict[int, SegmentDecision] = {}
        unnamed = list(profiles)

        detectors: tuple[tuple[str, Callable[[Dict[str, Any], List[Dict[str, Any]]], Optional[SegmentDecision]]], ...] = (
            ("At Risk Customers", self._detect_at_risk),
            ("International Customers", self._detect_international),
            ("Data Driven Customers", self._detect_data_driven),
            ("Digital Enthusiast Customers", self._detect_digital_enthusiast),
            ("Voice Focused Customers", self._detect_voice_focused),
            ("Loyal Customers", self._detect_loyal),
            ("New Customers", self._detect_new),
            ("Dormant Customers", self._detect_dormant),
            ("Growth Potential Customers", self._detect_growth_potential),
            ("Budget Conscious Customers", self._detect_budget_conscious),
        )

        unique_special_segments = {
            "At Risk Customers",
            "International Customers",
            "Data Driven Customers",
            "Voice Focused Customers",
        }

        for segment_name, detector in detectors:
            candidates = []
            for profile in unnamed:
                decision = detector(profile, profiles)
                if decision is not None and decision.name in APPROVED_SEGMENTS:
                    candidates.append((profile, decision))

            if not candidates:
                continue

            candidates.sort(key=lambda item: item[1].confidence, reverse=True)
            if segment_name in unique_special_segments:
                if segment_name == "At Risk Customers" and self._all_at_risk_candidates_are_severe(candidates, profiles):
                    selected = candidates
                else:
                    selected = candidates[:1]
            else:
                selected = candidates

            for profile, decision in selected:
                cluster_id = int(profile["cluster_id"])
                if cluster_id not in decisions:
                    decisions[cluster_id] = decision
                    unnamed.remove(profile)

        self._assign_value_fallbacks(unnamed, profiles, decisions)
        return decisions

    def _assign_value_fallbacks(
        self,
        unnamed: List[Dict[str, Any]],
        all_profiles: List[Dict[str, Any]],
        decisions: Dict[int, SegmentDecision],
    ) -> None:
        if not unnamed:
            return

        ordered = self._sort_by(unnamed, "value_score")
        labels = self._value_labels_for_count(ordered, all_profiles)
        total = len(all_profiles)

        for profile, segment_name in zip(ordered, labels):
            rank = int(profile.get("value_rank", total))
            decisions[int(profile["cluster_id"])] = SegmentDecision(
                name=segment_name,
                confidence=self._round(float(profile.get("value_score", 0.0)), 4),
                explanation=(
                    f"Assigned {segment_name} because this unnamed cluster ranks "
                    f"#{rank} of {total} by value_score after special segment confidence checks."
                ),
            )

    def _value_labels_for_count(
        self,
        ordered_profiles: List[Dict[str, Any]],
        all_profiles: List[Dict[str, Any]],
    ) -> List[str]:
        count = len(ordered_profiles)
        if count <= 0:
            return []
        if count == 1:
            profile = ordered_profiles[0]
            if self._can_be_low_value(profile, all_profiles):
                return ["Low Value Customers"]
            if self._can_be_premium(profile):
                return ["Premium Customers"]
            return ["Medium Value Customers"]
        if count == 2:
            return [
                "Premium Customers",
                self._low_or_budget_or_medium(ordered_profiles[-1], all_profiles),
            ]
        if count == 3:
            return [
                "Premium Customers",
                "Medium Value Customers",
                self._low_or_budget_or_medium(ordered_profiles[-1], all_profiles),
            ]
        return (
            ["Premium Customers", "High Value Customers"]
            + ["Medium Value Customers"] * (count - 3)
            + [self._low_or_budget_or_medium(ordered_profiles[-1], all_profiles)]
        )

    def _validate_final_ordering(
        self,
        profiles: List[Dict[str, Any]],
        decisions: Dict[int, SegmentDecision],
    ) -> None:
        value_profiles = [
            profile
            for profile in profiles
            if decisions[int(profile["cluster_id"])].name in VALUE_SEGMENT_ORDER
        ]
        if len(value_profiles) < 2:
            return

        ordered_profiles = self._sort_by(value_profiles, "value_score")
        ordered_labels = sorted(
            [decisions[int(profile["cluster_id"])].name for profile in value_profiles],
            key=lambda label: VALUE_SEGMENT_ORDER.index(label),
        )

        for profile, label in zip(ordered_profiles, ordered_labels):
            cluster_id = int(profile["cluster_id"])
            if decisions[cluster_id].name != label:
                decisions[cluster_id] = SegmentDecision(
                    name=label,
                    confidence=self._round(float(profile.get("value_score", 0.0)), 4),
                    explanation=(
                        f"Assigned {label} after final value ordering validation because "
                        f"this cluster ranks #{profile.get('value_rank')} by value_score."
                    ),
                )

    def _validate_final_assignments(
        self,
        profiles: List[Dict[str, Any]],
        decisions: Dict[int, SegmentDecision],
    ) -> None:
        """Replace labels that contradict final metrics with valid fallbacks."""
        for profile in profiles:
            cluster_id = int(profile["cluster_id"])
            decision = decisions[cluster_id]
            replacement: Optional[str] = None

            if decision.name == "At Risk Customers" and self._detect_at_risk(profile, profiles) is None:
                replacement = self._best_value_fallback(profile, profiles)
            elif decision.name == "Low Value Customers" and not self._can_be_low_value(profile, profiles):
                replacement = self._best_value_fallback(profile, profiles, exclude_low=True)
            elif decision.name == "Premium Customers" and not self._can_be_premium(profile):
                replacement = self._best_value_fallback(profile, profiles, exclude_premium=True)
            elif decision.name == "High Value Customers" and profile["value_score"] < self._median(profiles, "value_score"):
                replacement = "Medium Value Customers"

            if replacement and replacement != decision.name:
                decisions[cluster_id] = SegmentDecision(
                    name=replacement,
                    confidence=self._round(float(profile.get("value_score", 0.0)), 4),
                    explanation=(
                        f"Assigned {replacement} after final validation because the previous "
                        f"{decision.name} label contradicted this cluster's metrics."
                    ),
                )

        self._validate_final_ordering(profiles, decisions)

    def _build_business_segment_cards(
        self,
        clusters: List[Dict[str, Any]],
        total_customers: int,
    ) -> List[Dict[str, Any]]:
        cards = []
        for cluster in sorted(clusters, key=lambda item: int(item["cluster_id"])):
            card = {
                "business_segment": cluster["business_segment"],
                "name": cluster["business_segment"],
                "cluster_id": int(cluster["cluster_id"]),
                "customer_count": int(cluster["customer_count"]),
                "percentage": self._percentage(cluster["customer_count"], total_customers),
                "source_cluster_ids": [int(cluster["cluster_id"])],
                "rule_version": SEGMENTATION_RULE_VERSION,
                "naming_source": NAMING_SOURCE,
                "naming_confidence": cluster["naming_confidence"],
                "explanation": cluster["explanation"],
                "value_score": cluster["value_score"],
                "risk_score": cluster["risk_score"],
                "data_score": cluster["data_score"],
                "international_score": cluster["international_score"],
                "loyalty_score": cluster["loyalty_score"],
                "growth_score": cluster["growth_score"],
                "avg_arpu": cluster["avg_arpu"],
                "avg_data_usage": cluster["avg_data_usage"],
                "avg_voice_minutes": cluster["avg_voice_minutes"],
                "avg_international_minutes": cluster["avg_international_minutes"],
                "avg_clv": cluster["avg_clv"],
                "avg_satisfaction": cluster["avg_satisfaction"],
                "avg_complaints": cluster["avg_complaints"],
                "avg_late_payments": cluster["avg_late_payments"],
                "avg_tenure_months": cluster["avg_tenure_months"],
                "avg_churn_probability": cluster["avg_churn_probability"],
                "validation_warnings": cluster["validation_warnings"],
            }
            cards.append(card)
        return cards

    def _detect_at_risk(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        evidence = self._at_risk_evidence(profile)
        if not evidence or self._is_protected_from_at_risk(profile):
            return None

        return SegmentDecision(
            "At Risk Customers",
            self._round(max(float(profile["risk_score"]), 0.7), 4),
            f"Assigned At Risk Customers because {'; '.join(evidence)}.",
        )

    def _detect_international(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        clear_top = self._is_clear_top(profile, profiles, "international_score")
        significant = profile["avg_international_minutes"] >= max(150.0, self._mean(profiles, "avg_international_minutes") * 1.5)
        if not (clear_top and significant and profile["avg_arpu"] >= self._median(profiles, "avg_arpu") * 0.75):
            return None
        return SegmentDecision(
            "International Customers",
            profile["international_score"],
            "Assigned International Customers because this cluster has the highest international_score and international minutes are significantly above average.",
        )

    def _detect_data_driven(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        clear_top = self._is_clear_top(profile, profiles, "data_score")
        exceptional_data = profile["avg_data_usage"] >= max(250.0, self._mean(profiles, "avg_data_usage") * 1.5)
        voice_not_dominant = profile["data_usage_score"] >= profile["voice_usage_score"]
        if not (clear_top and exceptional_data and voice_not_dominant):
            return None
        return SegmentDecision(
            "Data Driven Customers",
            profile["data_score"],
            "Assigned Data Driven Customers because this cluster has the highest data_score and data usage is significantly above average.",
        )

    def _detect_digital_enthusiast(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        strong_value = profile["value_score"] >= 0.70 or profile["value_rank"] == 1
        strong_data = (
            profile["data_usage_score"] >= 0.75
            and profile["avg_data_usage"] >= max(150.0, self._mean(profiles, "avg_data_usage") * 1.5)
        )
        if not (strong_value and strong_data and profile["digital_score"] >= 0.72):
            return None
        return SegmentDecision(
            "Digital Enthusiast Customers",
            profile["digital_score"],
            "Assigned Digital Enthusiast Customers because this cluster combines high value_score with very strong data engagement.",
        )

    def _detect_voice_focused(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        if not (
            self._is_clear_top(profile, profiles, "voice_score")
            and profile["voice_usage_score"] >= 0.75
            and profile["voice_usage_score"] > profile["data_usage_score"] + 0.20
        ):
            return None
        return SegmentDecision(
            "Voice Focused Customers",
            profile["voice_score"],
            "Assigned Voice Focused Customers because voice minutes dominate this cluster and voice_score is clearly highest.",
        )

    def _detect_loyal(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        if not (
            self._is_clear_top(profile, profiles, "loyalty_score")
            and profile["tenure_score"] >= 0.75
            and profile["avg_satisfaction"] >= 7.5
            and profile["avg_complaints"] < 1
            and profile["avg_churn_probability"] < 40
        ):
            return None
        return SegmentDecision(
            "Loyal Customers",
            profile["loyalty_score"],
            "Assigned Loyal Customers because this cluster has exceptional tenure, good satisfaction, and low churn probability.",
        )

    def _detect_new(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        if not (
            profile["tenure_score"] <= 0.15
            and self._is_clear_bottom(profile, profiles, "avg_tenure_months")
            and profile["avg_tenure_months"] <= self._mean(profiles, "avg_tenure_months") * 0.55
        ):
            return None
        return SegmentDecision(
            "New Customers",
            self._round(1 - float(profile["tenure_score"]), 4),
            "Assigned New Customers because this cluster has the clearly lowest tenure compared with all clusters.",
        )

    def _detect_dormant(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        low_activity = (
            profile["data_usage_score"] <= 0.15
            and profile["voice_usage_score"] <= 0.15
            and profile["avg_data_usage"] < 5
            and profile["avg_voice_minutes"] < 30
        )
        low_revenue = profile["arpu_score"] <= 0.20 and profile["avg_arpu"] <= self._median(profiles, "avg_arpu")
        if not (low_activity and low_revenue and profile["dormant_score"] >= 0.75):
            return None
        return SegmentDecision(
            "Dormant Customers",
            profile["dormant_score"],
            "Assigned Dormant Customers because this cluster has extremely low activity, low usage, and low ARPU.",
        )

    def _detect_growth_potential(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        medium_value = 0.35 <= profile["value_score"] <= 0.72
        strong_usage = profile["data_usage_score"] >= 0.45 or profile["voice_usage_score"] >= 0.45
        healthy = profile["avg_satisfaction"] >= 6 and profile["avg_churn_probability"] < 60
        not_top_value = profile["value_rank"] > 1
        if not (medium_value and strong_usage and healthy and not_top_value and profile["growth_score"] >= 0.70):
            return None
        return SegmentDecision(
            "Growth Potential Customers",
            profile["growth_score"],
            "Assigned Growth Potential Customers because this cluster has medium value_score, strong usage, good satisfaction, and churn probability below 60%.",
        )

    def _detect_budget_conscious(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> Optional[SegmentDecision]:
        low_arpu = profile["arpu_score"] <= 0.25 and profile["avg_arpu"] < self._median(profiles, "avg_arpu")
        active_usage = profile["avg_data_usage"] >= 20 or profile["avg_voice_minutes"] >= 100
        acceptable_satisfaction = profile["avg_satisfaction"] >= 6
        if not (low_arpu and active_usage and acceptable_satisfaction and profile["budget_score"] >= 0.58):
            return None
        return SegmentDecision(
            "Budget Conscious Customers",
            profile["budget_score"],
            "Assigned Budget Conscious Customers because this cluster has low ARPU but active usage and acceptable satisfaction.",
        )

    def _at_risk_evidence(self, profile: Dict[str, Any]) -> List[str]:
        if profile["avg_churn_probability"] >= 60:
            return ["churn_probability is at least 60%"]

        evidence = []
        if profile["avg_complaints"] >= 2:
            evidence.append("complaints are at least 2")
        if profile["avg_late_payments"] >= 3:
            evidence.append("late payments are at least 3")
        if profile["avg_satisfaction"] < 6:
            evidence.append("satisfaction is below 6")
        if profile["data_usage_score"] <= 0.25:
            evidence.append("data usage is in the bottom quartile")
        if profile["voice_usage_score"] <= 0.25:
            evidence.append("voice usage is in the bottom quartile")
        if profile["tenure_score"] <= 0.25:
            evidence.append("tenure is in the bottom quartile")

        return evidence if len(evidence) >= 2 else []

    def _is_protected_from_at_risk(self, profile: Dict[str, Any]) -> bool:
        return (
            profile["avg_satisfaction"] >= 7
            and profile["avg_complaints"] < 1
            and self._is_active(profile)
        )

    def _is_severe_at_risk(self, profile: Dict[str, Any]) -> bool:
        evidence = self._at_risk_evidence(profile)
        return profile["avg_churn_probability"] >= 60 or len(evidence) >= 3

    def _all_at_risk_candidates_are_severe(
        self,
        candidates: List[tuple[Dict[str, Any], SegmentDecision]],
        profiles: List[Dict[str, Any]],
    ) -> bool:
        return len(candidates) > 1 and all(self._is_severe_at_risk(profile) for profile, _ in candidates)

    def _can_be_premium(self, profile: Dict[str, Any]) -> bool:
        return profile["value_rank"] == 1 or profile["value_score"] >= 0.75 or profile["avg_arpu"] >= 100

    def _can_be_low_value(self, profile: Dict[str, Any], profiles: List[Dict[str, Any]]) -> bool:
        protected_valuable = (
            profile["avg_arpu"] > 100
            and profile["avg_satisfaction"] >= 7
            and self._is_active(profile)
        )
        if protected_valuable:
            return False

        near_weakest = (
            profile["value_rank"] == len(profiles)
            or profile["value_score"] <= self._percentile(profiles, "value_score", 25)
        )
        weak_arpu = profile["avg_arpu"] <= self._percentile(profiles, "avg_arpu", 35)
        weak_clv = profile["avg_clv"] <= self._percentile(profiles, "avg_clv", 35)
        weak_engagement = profile["data_usage_score"] <= 0.35 and profile["voice_usage_score"] <= 0.35
        return near_weakest and (weak_arpu or weak_clv or weak_engagement)

    def _low_or_budget_or_medium(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
    ) -> str:
        if self._can_be_low_value(profile, profiles):
            return "Low Value Customers"
        if self._detect_budget_conscious(profile, profiles) is not None:
            return "Budget Conscious Customers"
        return "Medium Value Customers"

    def _best_value_fallback(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
        exclude_low: bool = False,
        exclude_premium: bool = False,
    ) -> str:
        if not exclude_premium and self._can_be_premium(profile):
            return "Premium Customers" if profile["value_rank"] == 1 else "High Value Customers"
        if profile["value_score"] >= self._percentile(profiles, "value_score", 65):
            return "High Value Customers"
        if not exclude_low and self._can_be_low_value(profile, profiles):
            return "Low Value Customers"
        if self._detect_budget_conscious(profile, profiles) is not None:
            return "Budget Conscious Customers"
        return "Medium Value Customers"

    def _validate_assignment(
        self,
        profile: Dict[str, Any],
        segment_name: str,
        profiles: List[Dict[str, Any]],
    ) -> List[str]:
        warnings: List[str] = []

        if segment_name == "At Risk Customers" and self._detect_at_risk(profile, profiles) is None:
            warnings.append("At Risk Customers requires strong churn or at least two risk evidence signals.")
        if segment_name == "Low Value Customers" and not self._can_be_low_value(profile, profiles):
            warnings.append("Low Value Customers requires the weakest or near-weakest commercial value profile.")
        if segment_name == "Premium Customers" and not self._can_be_premium(profile):
            warnings.append("Premium Customers requires one of the strongest value profiles.")
        if segment_name == "International Customers" and self._detect_international(profile, profiles) is None:
            warnings.append("International Customers requires clearly highest international behavior.")
        if segment_name == "Data Driven Customers" and self._detect_data_driven(profile, profiles) is None:
            warnings.append("Data Driven Customers requires clearly exceptional data behavior.")
        if segment_name == "Digital Enthusiast Customers" and self._detect_digital_enthusiast(profile, profiles) is None:
            warnings.append("Digital Enthusiast Customers requires strong value and strong data engagement.")
        if segment_name == "Voice Focused Customers" and self._detect_voice_focused(profile, profiles) is None:
            warnings.append("Voice Focused Customers requires clearly dominant voice usage.")
        if segment_name == "Loyal Customers" and self._detect_loyal(profile, profiles) is None:
            warnings.append("Loyal Customers requires exceptional tenure, satisfaction, and low churn.")
        if segment_name == "New Customers" and self._detect_new(profile, profiles) is None:
            warnings.append("New Customers requires clearly lowest tenure.")
        if segment_name == "Dormant Customers" and self._detect_dormant(profile, profiles) is None:
            warnings.append("Dormant Customers requires very low activity, usage, and ARPU.")
        if segment_name == "Growth Potential Customers" and self._detect_growth_potential(profile, profiles) is None:
            warnings.append("Growth Potential Customers requires medium value, usage strength, satisfaction >= 6, and churn < 60%.")
        if segment_name == "Budget Conscious Customers" and self._detect_budget_conscious(profile, profiles) is None:
            warnings.append("Budget Conscious Customers requires low ARPU, active usage, and acceptable satisfaction.")

        return warnings

    def _normalized_values(self, profiles: List[Dict[str, Any]], metric: str) -> List[float]:
        values = [float(profile[metric]) for profile in profiles]
        low = min(values)
        high = max(values)
        if high == low:
            return [0.5 for _ in values]
        return [(value - low) / (high - low) for value in values]

    def _is_clear_top(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
        score_name: str,
        margin: float = 0.12,
    ) -> bool:
        ordered = self._sort_by(profiles, score_name)
        if not ordered or ordered[0]["cluster_id"] != profile["cluster_id"]:
            return False
        if len(ordered) == 1:
            return float(profile.get(score_name, 0)) >= 0.70
        return float(ordered[0].get(score_name, 0)) >= float(ordered[1].get(score_name, 0)) + margin

    def _is_clear_bottom(
        self,
        profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
        metric_name: str,
        margin_ratio: float = 0.20,
    ) -> bool:
        ordered = sorted(profiles, key=lambda item: float(item.get(metric_name, 0)))
        if not ordered or ordered[0]["cluster_id"] != profile["cluster_id"]:
            return False
        if len(ordered) == 1:
            return False
        lowest = float(ordered[0].get(metric_name, 0))
        second = float(ordered[1].get(metric_name, 0))
        return lowest <= second * (1 - margin_ratio)

    def _is_active(self, profile: Dict[str, Any]) -> bool:
        return (
            profile["data_usage_score"] >= 0.40
            or profile["voice_usage_score"] >= 0.40
            or profile["avg_data_usage"] >= 20
            or profile["avg_voice_minutes"] >= 100
        )

    def _above_cluster_norm(self, profile: Dict[str, Any], score_name: str, threshold: float) -> bool:
        return float(profile.get(score_name, 0.0)) >= threshold

    def _below_cluster_norm(self, profile: Dict[str, Any], score_name: str, threshold: float) -> bool:
        return float(profile.get(score_name, 0.0)) <= threshold

    def _sort_by(self, profiles: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
        return sorted(
            profiles,
            key=lambda profile: (
                float(profile.get(key, 0.0)),
                float(profile.get("avg_arpu", 0.0)),
                float(profile.get("avg_clv", 0.0)),
                -int(profile.get("cluster_id", 0)),
            ),
            reverse=True,
        )

    def _mean(self, profiles: List[Dict[str, Any]], key: str) -> float:
        if not profiles:
            return 0.0
        return float(np.mean([float(profile.get(key, 0.0)) for profile in profiles]))

    def _median(self, profiles: List[Dict[str, Any]], key: str) -> float:
        if not profiles:
            return 0.0
        return float(np.median([float(profile.get(key, 0.0)) for profile in profiles]))

    def _percentile(self, profiles: List[Dict[str, Any]], key: str, percentile: float) -> float:
        if not profiles:
            return 0.0
        return float(np.percentile([float(profile.get(key, 0.0)) for profile in profiles], percentile))

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
