from pathlib import Path

import pandas as pd

from segmentation_engine.api.business_segmentation import (
    BROAD_SEGMENTS,
    BusinessSegmentationService,
    NAMING_SOURCE,
    SEGMENTATION_RULE_VERSION,
)
from segmentation_engine.api.services import SegmentationService


def rows(cluster_id, count, **metrics):
    defaults = {
        "monthly_spend": 10,
        "data_consumption_gb": 1,
        "voice_minutes": 20,
        "international_calls_min": 0,
        "clv": 0,
        "satisfaction_score": 8,
        "complaint_count": 0,
        "late_payments": 0,
        "tenure_months": 12,
        "churn_risk": 0.1,
    }
    defaults.update(metrics)
    return [defaults.copy() | {"expected_cluster": cluster_id} for _ in range(count)]


def segment_from_profiles(profiles, k):
    data_rows = []
    labels = []
    for cluster_id, count, metrics in profiles:
        data_rows.extend(rows(cluster_id, count, **metrics))
        labels.extend([cluster_id] * count)

    df = pd.DataFrame(data_rows).drop(columns=["expected_cluster"])
    return BusinessSegmentationService().segment_clusters(df, labels, mode_cluster_count=k)


def segment_names(result):
    return {cluster["cluster_id"]: cluster["business_segment"] for cluster in result["clusters"]}


def test_segment_names_are_metric_based_not_cluster_id_based():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 8, "data_consumption_gb": 1}),
            (1, 2, {"monthly_spend": 160, "data_consumption_gb": 120}),
        ],
        k=2,
    )

    names = segment_names(result)
    assert names[0] == "Low Value Customers"
    assert names[1] == "High Value Customers"


def test_k_lte_5_only_uses_broad_segment_names():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 80, "international_calls_min": 220}),
            (1, 2, {"monthly_spend": 50, "data_consumption_gb": 300, "voice_minutes": 100}),
            (2, 2, {"monthly_spend": 160, "data_consumption_gb": 120}),
            (3, 2, {"monthly_spend": 30}),
            (4, 2, {"monthly_spend": 10}),
        ],
        k=5,
    )

    assert {cluster["business_segment"] for cluster in result["clusters"]}.issubset(BROAD_SEGMENTS)


def test_k4_returns_four_unique_ranked_business_segments():
    result = segment_from_profiles(
        [
            (7, 2, {"monthly_spend": 30, "data_consumption_gb": 20, "churn_risk": 0.9}),
            (2, 2, {"monthly_spend": 160, "data_consumption_gb": 120, "churn_risk": 0.1}),
            (5, 2, {"monthly_spend": 95, "data_consumption_gb": 70, "churn_risk": 0.1}),
            (1, 2, {"monthly_spend": 15, "data_consumption_gb": 5, "churn_risk": 0.1}),
        ],
        k=4,
    )

    cards = result["business_segments"]
    names = segment_names(result)
    assert len(cards) == 4
    assert len(set(names.values())) == 4
    assert names[7] == "At Risk Customers"
    assert names[2] == "Premium Customers"
    assert names[5] == "High Value Customers"
    assert names[1] == "Low Value Customers"


def test_k4_skips_at_risk_when_no_cluster_is_clearly_risky():
    result = segment_from_profiles(
        [
            (4, 2, {"monthly_spend": 150, "data_consumption_gb": 120, "churn_risk": 0.1}),
            (8, 2, {"monthly_spend": 90, "data_consumption_gb": 70, "churn_risk": 0.1}),
            (2, 2, {"monthly_spend": 45, "data_consumption_gb": 35, "churn_risk": 0.1}),
            (6, 2, {"monthly_spend": 15, "data_consumption_gb": 5, "churn_risk": 0.1}),
        ],
        k=4,
    )

    names = segment_names(result)
    assert "At Risk Customers" not in set(names.values())
    assert names[4] == "Premium Customers"
    assert names[8] == "High Value Customers"
    assert names[2] == "Medium Value Customers"
    assert names[6] == "Low Value Customers"


def test_k5_returns_five_unique_ranked_business_segments():
    result = segment_from_profiles(
        [
            (4, 2, {"monthly_spend": 25, "data_consumption_gb": 10, "churn_risk": 0.9}),
            (9, 2, {"monthly_spend": 180, "data_consumption_gb": 120, "churn_risk": 0.1}),
            (1, 2, {"monthly_spend": 100, "data_consumption_gb": 80, "churn_risk": 0.1}),
            (6, 2, {"monthly_spend": 45, "data_consumption_gb": 40, "churn_risk": 0.1}),
            (3, 2, {"monthly_spend": 10, "data_consumption_gb": 5, "churn_risk": 0.1}),
        ],
        k=5,
    )

    cards = result["business_segments"]
    names = segment_names(result)
    assert len(cards) == 5
    assert len(set(names.values())) == 5
    assert names[4] == "At Risk Customers"
    assert names[9] == "Premium Customers"
    assert names[1] == "High Value Customers"
    assert names[6] == "Medium Value Customers"
    assert names[3] == "Low Value Customers"


def test_value_score_prioritizes_revenue_data_and_clv_over_voice():
    result = segment_from_profiles(
        [
            (4, 2, {"monthly_spend": 15, "data_consumption_gb": 5, "voice_minutes": 20, "clv": 150, "churn_risk": 0.9}),
            (9, 2, {"monthly_spend": 120, "data_consumption_gb": 120, "voice_minutes": 200, "clv": 1200, "churn_risk": 0.1}),
            (1, 2, {"monthly_spend": 80, "data_consumption_gb": 80, "voice_minutes": 300, "clv": 800, "churn_risk": 0.1}),
            (6, 2, {"monthly_spend": 32, "data_consumption_gb": 24, "voice_minutes": 900, "clv": 320, "churn_risk": 0.1}),
            (3, 2, {"monthly_spend": 36, "data_consumption_gb": 121, "voice_minutes": 50, "clv": 360, "churn_risk": 0.1}),
        ],
        k=5,
    )

    clusters = {cluster["cluster_id"]: cluster for cluster in result["clusters"]}
    names = segment_names(result)
    assert clusters[3]["value_score"] > clusters[6]["value_score"]
    assert names[3] == "Medium Value Customers"
    assert names[6] == "Low Value Customers"


def test_low_and_medium_are_swapped_when_low_has_stronger_arpu_and_data():
    service = BusinessSegmentationService()
    medium_profile = {
        "cluster_id": 1,
        "avg_arpu": 32,
        "avg_data_usage": 24,
        "avg_voice_minutes": 900,
        "avg_clv": 320,
        "customer_count": 10,
        "value_score": 0.25,
    }
    low_profile = {
        "cluster_id": 2,
        "avg_arpu": 36,
        "avg_data_usage": 121,
        "avg_voice_minutes": 50,
        "avg_clv": 360,
        "customer_count": 10,
        "value_score": 0.2,
    }
    segment_by_cluster = {
        1: "Medium Value Customers",
        2: "Low Value Customers",
    }

    service._swap_low_medium_when_low_is_stronger(
        [medium_profile, low_profile],
        segment_by_cluster,
    )

    assert segment_by_cluster[1] == "Low Value Customers"
    assert segment_by_cluster[2] == "Medium Value Customers"


def test_exact_wrong_medium_low_case_is_corrected():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 160, "data_consumption_gb": 140, "voice_minutes": 300, "clv": 30, "tenure_months": 95, "churn_risk": 0.1}),
            (1, 2, {"monthly_spend": 95, "data_consumption_gb": 80, "voice_minutes": 400, "clv": 20, "tenure_months": 92, "churn_risk": 0.1}),
            (2, 2, {"monthly_spend": 15, "data_consumption_gb": 5, "voice_minutes": 10, "clv": 2, "tenure_months": 10, "churn_risk": 0.9}),
            (4, 2, {"monthly_spend": 32.14, "data_consumption_gb": 24.741, "voice_minutes": 902.29, "clv": 10.244, "tenure_months": 90.689, "churn_risk": 0.1}),
            (3, 2, {"monthly_spend": 36.18, "data_consumption_gb": 121.216, "voice_minutes": 146.937, "clv": 11.479, "tenure_months": 88.582, "churn_risk": 0.1}),
        ],
        k=5,
    )

    names = segment_names(result)
    clusters = {cluster["cluster_id"]: cluster for cluster in result["clusters"]}
    assert names[3] == "Medium Value Customers"
    assert names[4] == "Low Value Customers"
    assert clusters[3]["value_score"] > clusters[4]["value_score"]


def test_api_segments_include_debug_naming_fields():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 8, "data_consumption_gb": 1}),
            (1, 2, {"monthly_spend": 160, "data_consumption_gb": 120}),
        ],
        k=2,
    )

    assert result["segmentation_rule_version"] == SEGMENTATION_RULE_VERSION
    assert result["naming_source"] == NAMING_SOURCE
    for cluster in result["clusters"]:
        assert cluster["rule_version"] == SEGMENTATION_RULE_VERSION
        assert cluster["naming_source"] == NAMING_SOURCE
        assert "value_score" in cluster
        assert "risk_score" in cluster
    for segment in result["business_segments"]:
        assert segment["rule_version"] == SEGMENTATION_RULE_VERSION
        assert segment["naming_source"] == NAMING_SOURCE
        assert "value_score" in segment
        assert "risk_score" in segment


def test_k_gt_5_can_use_detailed_segment_names():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 70, "international_calls_min": 200}),
            (1, 2, {"monthly_spend": 45, "data_consumption_gb": 260, "voice_minutes": 100}),
            (2, 2, {"monthly_spend": 45, "data_consumption_gb": 80, "churn_risk": 0.2}),
            (3, 2, {"monthly_spend": 160, "data_consumption_gb": 120}),
            (4, 2, {"monthly_spend": 80}),
            (5, 2, {"monthly_spend": 10}),
        ],
        k=6,
    )

    names = set(segment_names(result).values())
    assert "International Customers" in names
    assert "Data Driven Customers" in names
    assert "Growth Potential Customers" in names


def test_medium_churn_alone_does_not_make_all_clusters_at_risk():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 35, "churn_risk": 0.55}),
            (1, 2, {"monthly_spend": 85, "churn_risk": 0.55}),
            (2, 2, {"monthly_spend": 155, "data_consumption_gb": 120, "churn_risk": 0.55}),
        ],
        k=3,
    )

    assert set(segment_names(result).values()) != {"At Risk Customers"}
    assert "All customers were classified as At Risk" not in " ".join(result["warnings"])


def test_k2_uses_risk_then_value_ranking():
    result = segment_from_profiles(
        [
            (10, 2, {"monthly_spend": 25, "data_consumption_gb": 5, "churn_risk": 0.95}),
            (2, 2, {"monthly_spend": 130, "data_consumption_gb": 120, "churn_risk": 0.1}),
        ],
        k=2,
    )

    names = segment_names(result)
    assert names[10] == "At Risk Customers"
    assert names[2] == "High Value Customers"


def test_k2_without_clear_risk_uses_high_and_low_value():
    result = segment_from_profiles(
        [
            (9, 2, {"monthly_spend": 30, "data_consumption_gb": 20, "churn_risk": 0.1}),
            (1, 2, {"monthly_spend": 120, "data_consumption_gb": 100, "churn_risk": 0.1}),
        ],
        k=2,
    )

    names = segment_names(result)
    assert names[1] == "High Value Customers"
    assert names[9] == "Low Value Customers"


def test_k3_with_clear_risk_uses_at_risk_high_and_low():
    result = segment_from_profiles(
        [
            (3, 2, {"monthly_spend": 20, "data_consumption_gb": 5, "churn_risk": 0.9}),
            (1, 2, {"monthly_spend": 140, "data_consumption_gb": 110, "churn_risk": 0.1}),
            (7, 2, {"monthly_spend": 35, "data_consumption_gb": 20, "churn_risk": 0.1}),
        ],
        k=3,
    )

    names = segment_names(result)
    assert names[3] == "At Risk Customers"
    assert names[1] == "High Value Customers"
    assert names[7] == "Low Value Customers"


def test_k3_without_clear_risk_uses_premium_medium_low():
    result = segment_from_profiles(
        [
            (8, 2, {"monthly_spend": 90, "data_consumption_gb": 80, "churn_risk": 0.1}),
            (4, 2, {"monthly_spend": 45, "data_consumption_gb": 35, "churn_risk": 0.1}),
            (2, 2, {"monthly_spend": 15, "data_consumption_gb": 10, "churn_risk": 0.1}),
        ],
        k=3,
    )

    names = segment_names(result)
    assert names[8] == "Premium Customers"
    assert names[4] == "Medium Value Customers"
    assert names[2] == "Low Value Customers"


def test_common_late_payment_noise_does_not_swamp_k6_segments():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 31, "data_consumption_gb": 24, "voice_minutes": 900, "late_payments": 6.04}),
            (1, 2, {"monthly_spend": 40, "data_consumption_gb": 128, "voice_minutes": 157, "late_payments": 9.57}),
            (2, 2, {"monthly_spend": 143, "international_calls_min": 540, "late_payments": 5.95}),
            (3, 2, {"monthly_spend": 297, "data_consumption_gb": 462, "international_calls_min": 249, "late_payments": 5.98}),
            (4, 2, {"monthly_spend": 31, "data_consumption_gb": 113, "voice_minutes": 156, "late_payments": 5.79}),
            (5, 2, {"monthly_spend": 46, "data_consumption_gb": 123, "voice_minutes": 160, "late_payments": 2.54}),
        ],
        k=6,
    )

    names = segment_names(result)
    assert names[0] == "Medium Value Customers"
    assert names[1] == "At Risk Customers"
    assert names[2] == "International Customers"
    assert names[3] == "International Customers"
    assert names[5] == "Growth Potential Customers"
    assert sum(name == "At Risk Customers" for name in names.values()) == 1


def test_detailed_mode_splits_middle_arpu_more_strictly_for_k7():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 24, "data_consumption_gb": 20}),
            (1, 2, {"monthly_spend": 35, "data_consumption_gb": 40}),
            (2, 2, {"monthly_spend": 65, "data_consumption_gb": 80}),
            (3, 2, {"monthly_spend": 95, "data_consumption_gb": 45}),
            (4, 2, {"monthly_spend": 170, "data_consumption_gb": 120}),
            (5, 2, {"monthly_spend": 70, "international_calls_min": 180}),
            (6, 2, {"monthly_spend": 50, "data_consumption_gb": 270, "voice_minutes": 100}),
        ],
        k=7,
    )

    names = segment_names(result)
    assert names[0] == "Low Value Customers"
    assert names[1] == "Medium Value Customers"
    assert names[2] == "Growth Potential Customers"
    assert names[3] == "High Value Customers"
    assert names[4] == "Premium Customers"
    assert names[5] == "International Customers"
    assert names[6] == "Data Driven Customers"


def test_k8_can_aggregate_duplicate_business_meanings_without_matching_k_cards():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 28, "data_consumption_gb": 20}),
            (1, 2, {"monthly_spend": 34, "data_consumption_gb": 40}),
            (2, 2, {"monthly_spend": 60, "data_consumption_gb": 90}),
            (3, 2, {"monthly_spend": 62, "data_consumption_gb": 110}),
            (4, 2, {"monthly_spend": 100}),
            (5, 2, {"monthly_spend": 160, "data_consumption_gb": 120}),
            (6, 2, {"monthly_spend": 75, "international_calls_min": 200}),
            (7, 2, {"monthly_spend": 55, "data_consumption_gb": 300, "voice_minutes": 120}),
        ],
        k=8,
    )

    cards = result["business_segments"]
    assert len(result["clusters"]) == 8
    assert len(cards) < 8
    assert any(segment["source_cluster_ids"] == [0, 1] for segment in cards)
    assert any(segment["source_cluster_ids"] == [2, 3] for segment in cards)


def test_international_is_detected_before_premium():
    result = segment_from_profiles(
        [(0, 3, {"monthly_spend": 180, "data_consumption_gb": 150, "international_calls_min": 200})],
        k=6,
    )

    assert segment_names(result)[0] == "International Customers"


def test_data_driven_is_detected_before_premium():
    result = segment_from_profiles(
        [(0, 3, {"monthly_spend": 180, "data_consumption_gb": 300, "voice_minutes": 100})],
        k=6,
    )

    assert segment_names(result)[0] == "Data Driven Customers"


def test_premium_medium_and_low_thresholds():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 150, "data_consumption_gb": 100}),
            (1, 2, {"monthly_spend": 45}),
            (2, 2, {"monthly_spend": 10}),
        ],
        k=3,
    )

    names = segment_names(result)
    assert names[0] == "Premium Customers"
    assert names[1] == "Medium Value Customers"
    assert names[2] == "Low Value Customers"


def test_duplicate_business_segments_are_aggregated_with_weighted_averages_for_detailed_mode():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 30, "data_consumption_gb": 10}),
            (1, 4, {"monthly_spend": 35, "data_consumption_gb": 40}),
            (2, 2, {"monthly_spend": 10, "data_consumption_gb": 5}),
            (3, 2, {"monthly_spend": 100, "data_consumption_gb": 40}),
            (4, 2, {"monthly_spend": 160, "data_consumption_gb": 120}),
            (5, 2, {"monthly_spend": 75, "international_calls_min": 200}),
        ],
        k=6,
    )

    medium_segments = [
        segment for segment in result["business_segments"]
        if segment["business_segment"] == "Medium Value Customers"
    ]

    assert len(medium_segments) == 1
    assert medium_segments[0]["source_cluster_ids"] == [0, 1]
    assert medium_segments[0]["customer_count"] == 6
    assert medium_segments[0]["avg_arpu"] == 33.333
    assert medium_segments[0]["avg_data_usage"] == 30


def test_export_frame_uses_business_segment_and_not_behavioral_group():
    df = pd.DataFrame(
        {
            "customer_id": ["A", "B"],
            "cluster_id": [0, 1],
            "business_segment": ["Medium Value Customers", "Premium Customers"],
            "monthly_spend": [45, 180],
            "data_consumption_gb": [20, 120],
            "voice_minutes": [100, 300],
            "tenure_months": [10, 20],
            "churn_risk": [0.2, 0.1],
        }
    )

    export_frame = SegmentationService()._build_customer_export_frame(df)

    assert "Business_Segment" in export_frame.columns
    assert "Original_Cluster_ID" in export_frame.columns
    assert "ARPU_TND" in export_frame.columns
    assert "Tenure_Months" in export_frame.columns
    assert "Behavioral_Group" not in export_frame.columns
    assert export_frame.loc[0, "Business_Segment"] == "Medium Value Customers"


def test_frontend_has_no_behavioral_subsegment_labels():
    frontend_root = Path(__file__).resolve().parents[1] / "frontend" / "src"
    source = "\n".join(path.read_text(encoding="utf-8") for path in frontend_root.rglob("*.ts*"))
    forbidden = [
        "Data-Heavy Power Users",
        "Highest Value",
        "Standard Value",
        "Economy",
        "Entry Level",
        "Behavioral_Group",
        "segmentSubtypeReason",
        "Data Heavy Streamers",
        "High Value Champions",
    ]

    for label in forbidden:
        assert label not in source
