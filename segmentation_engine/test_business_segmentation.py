from pathlib import Path

import pandas as pd

from segmentation_engine.api.business_segmentation import (
    APPROVED_SEGMENTS,
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
    first = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 8, "data_consumption_gb": 1}),
            (1, 2, {"monthly_spend": 160, "data_consumption_gb": 120, "clv": 1000}),
        ],
        k=2,
    )
    second = segment_from_profiles(
        [
            (99, 2, {"monthly_spend": 160, "data_consumption_gb": 120, "clv": 1000}),
            (7, 2, {"monthly_spend": 8, "data_consumption_gb": 1}),
        ],
        k=2,
    )

    assert segment_names(first)[1] == segment_names(second)[99]
    assert segment_names(first)[0] == segment_names(second)[7]


def test_only_approved_labels_are_returned_and_each_cluster_has_explanation():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 20, "data_consumption_gb": 10}),
            (1, 2, {"monthly_spend": 80, "data_consumption_gb": 80}),
            (2, 2, {"monthly_spend": 160, "data_consumption_gb": 120, "clv": 1200}),
        ],
        k=3,
    )

    for cluster in result["clusters"]:
        assert cluster["business_segment"] in APPROVED_SEGMENTS
        assert cluster["rule_version"] == SEGMENTATION_RULE_VERSION
        assert cluster["naming_source"] == NAMING_SOURCE
        assert cluster["explanation"]


def test_at_risk_is_not_forced_for_healthy_active_customers():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 36, "data_consumption_gb": 122, "satisfaction_score": 8, "complaint_count": 0, "tenure_months": 80, "churn_risk": 0.2}),
            (1, 2, {"monthly_spend": 80, "data_consumption_gb": 60, "satisfaction_score": 8, "complaint_count": 0, "tenure_months": 85, "churn_risk": 0.2}),
        ],
        k=2,
    )

    assert "At Risk Customers" not in set(segment_names(result).values())


def test_requested_healthy_active_cluster_cannot_be_at_risk():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 42.68, "data_consumption_gb": 92, "voice_minutes": 273, "satisfaction_score": 7.37, "complaint_count": 0.5, "churn_risk": 0.35}),
            (1, 2, {"monthly_spend": 120, "data_consumption_gb": 110, "voice_minutes": 320, "satisfaction_score": 8.2, "complaint_count": 0, "churn_risk": 0.1}),
            (2, 2, {"monthly_spend": 18, "data_consumption_gb": 6, "voice_minutes": 30, "satisfaction_score": 7.1, "complaint_count": 0, "churn_risk": 0.2}),
        ],
        k=3,
    )

    assert segment_names(result)[0] != "At Risk Customers"


def test_at_risk_requires_real_risk_evidence():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 25, "data_consumption_gb": 5, "satisfaction_score": 4, "complaint_count": 4, "churn_risk": 0.75}),
            (1, 2, {"monthly_spend": 100, "data_consumption_gb": 90, "satisfaction_score": 8, "churn_risk": 0.1}),
            (2, 2, {"monthly_spend": 45, "data_consumption_gb": 35, "satisfaction_score": 8, "churn_risk": 0.1}),
        ],
        k=3,
    )

    assert segment_names(result)[0] == "At Risk Customers"


def test_only_true_risky_clusters_receive_at_risk():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 20, "data_consumption_gb": 4, "voice_minutes": 15, "satisfaction_score": 5, "complaint_count": 3, "late_payments": 4, "churn_risk": 0.2}),
            (1, 2, {"monthly_spend": 42, "data_consumption_gb": 92, "voice_minutes": 273, "satisfaction_score": 7.3, "complaint_count": 0.5, "late_payments": 0, "churn_risk": 0.2}),
            (2, 2, {"monthly_spend": 90, "data_consumption_gb": 110, "voice_minutes": 300, "satisfaction_score": 8.2, "complaint_count": 0, "late_payments": 0, "churn_risk": 0.1}),
        ],
        k=3,
    )

    names = segment_names(result)
    assert names[0] == "At Risk Customers"
    assert names[1] != "At Risk Customers"
    assert names[2] != "At Risk Customers"


def test_international_is_not_forced_without_clear_behavior():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 70, "international_calls_min": 80}),
            (1, 2, {"monthly_spend": 90, "international_calls_min": 90}),
            (2, 2, {"monthly_spend": 40, "international_calls_min": 70}),
        ],
        k=3,
    )

    assert "International Customers" not in set(segment_names(result).values())


def test_international_requires_clear_top_international_minutes():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 70, "international_calls_min": 240}),
            (1, 2, {"monthly_spend": 90, "international_calls_min": 40}),
            (2, 2, {"monthly_spend": 40, "international_calls_min": 20}),
        ],
        k=3,
    )

    assert segment_names(result)[0] == "International Customers"


def test_data_driven_is_not_forced_without_exceptional_data_usage():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 70, "data_consumption_gb": 80, "voice_minutes": 100}),
            (1, 2, {"monthly_spend": 90, "data_consumption_gb": 95, "voice_minutes": 100}),
            (2, 2, {"monthly_spend": 40, "data_consumption_gb": 70, "voice_minutes": 100}),
        ],
        k=3,
    )

    assert "Data Driven Customers" not in set(segment_names(result).values())


def test_data_driven_requires_clear_exceptional_data_usage():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 70, "data_consumption_gb": 320, "voice_minutes": 100}),
            (1, 2, {"monthly_spend": 90, "data_consumption_gb": 80, "voice_minutes": 100}),
            (2, 2, {"monthly_spend": 40, "data_consumption_gb": 60, "voice_minutes": 100}),
        ],
        k=3,
    )

    assert segment_names(result)[0] == "Data Driven Customers"


def test_value_score_prioritizes_revenue_data_and_clv_over_voice():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 160, "data_consumption_gb": 120, "voice_minutes": 200, "clv": 1200}),
            (1, 2, {"monthly_spend": 32.14, "data_consumption_gb": 24.741, "voice_minutes": 902.29, "clv": 10.244, "tenure_months": 90.689}),
            (2, 2, {"monthly_spend": 36.18, "data_consumption_gb": 121.216, "voice_minutes": 146.937, "clv": 11.479, "tenure_months": 88.582}),
        ],
        k=3,
    )

    clusters = {cluster["cluster_id"]: cluster for cluster in result["clusters"]}
    assert clusters[2]["value_score"] > clusters[1]["value_score"]


def test_requested_valuable_customer_cannot_be_low_value():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 133, "data_consumption_gb": 142, "voice_minutes": 591, "tenure_months": 95, "satisfaction_score": 8.38, "clv": 900}),
            (1, 2, {"monthly_spend": 40, "data_consumption_gb": 40, "voice_minutes": 120, "tenure_months": 40, "satisfaction_score": 7, "clv": 120}),
            (2, 2, {"monthly_spend": 15, "data_consumption_gb": 4, "voice_minutes": 20, "tenure_months": 12, "satisfaction_score": 6.5, "clv": 20}),
        ],
        k=3,
    )

    assert segment_names(result)[0] != "Low Value Customers"


def test_value_fallback_ordering_keeps_premium_strongest_and_low_weakest():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 15, "data_consumption_gb": 5, "clv": 10}),
            (1, 2, {"monthly_spend": 45, "data_consumption_gb": 30, "clv": 200}),
            (2, 2, {"monthly_spend": 90, "data_consumption_gb": 70, "clv": 500}),
            (3, 2, {"monthly_spend": 180, "data_consumption_gb": 120, "clv": 1200}),
        ],
        k=4,
    )

    order = ["Premium Customers", "High Value Customers", "Medium Value Customers", "Low Value Customers"]
    value_clusters = [
        cluster
        for cluster in result["clusters"]
        if cluster["business_segment"] in set(order)
    ]
    scores_by_label = {
        cluster["business_segment"]: cluster["value_score"]
        for cluster in value_clusters
    }
    present_scores = [scores_by_label[label] for label in order if label in scores_by_label]

    assert present_scores == sorted(present_scores, reverse=True)
    assert scores_by_label["Premium Customers"] == max(present_scores)
    assert scores_by_label["Low Value Customers"] == min(present_scores)


def test_premium_and_low_value_extremes_are_valid_when_present():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 10, "data_consumption_gb": 2, "voice_minutes": 10, "clv": 5}),
            (1, 2, {"monthly_spend": 45, "data_consumption_gb": 35, "voice_minutes": 120, "clv": 100}),
            (2, 2, {"monthly_spend": 80, "data_consumption_gb": 80, "voice_minutes": 220, "clv": 500}),
            (3, 2, {"monthly_spend": 170, "data_consumption_gb": 150, "voice_minutes": 300, "clv": 1200}),
        ],
        k=4,
    )

    clusters = result["clusters"]
    premium = [cluster for cluster in clusters if cluster["business_segment"] == "Premium Customers"]
    low = [cluster for cluster in clusters if cluster["business_segment"] == "Low Value Customers"]
    if premium:
        assert premium[0]["value_score"] == max(cluster["value_score"] for cluster in clusters)
    if low:
        assert low[0]["value_score"] == min(cluster["value_score"] for cluster in clusters)


def test_special_segments_appear_only_with_confidence():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 50, "data_consumption_gb": 60, "international_calls_min": 70, "voice_minutes": 100}),
            (1, 2, {"monthly_spend": 55, "data_consumption_gb": 65, "international_calls_min": 75, "voice_minutes": 110}),
            (2, 2, {"monthly_spend": 60, "data_consumption_gb": 70, "international_calls_min": 80, "voice_minutes": 120}),
        ],
        k=3,
    )

    special_names = set(segment_names(result).values()) - {"Premium Customers", "High Value Customers", "Medium Value Customers", "Low Value Customers"}
    assert special_names == set()


def test_k_output_cards_match_selected_k_for_business_segments():
    result = segment_from_profiles(
        [
            (0, 2, {"monthly_spend": 20}),
            (1, 2, {"monthly_spend": 40}),
            (2, 2, {"monthly_spend": 60}),
            (3, 2, {"monthly_spend": 80}),
            (4, 2, {"monthly_spend": 100}),
            (5, 2, {"monthly_spend": 120}),
        ],
        k=6,
    )

    assert len(result["clusters"]) == 6
    assert len(result["business_segments"]) == 6
    assert all(segment["source_cluster_ids"] == [segment["cluster_id"]] for segment in result["business_segments"])


def test_k_2_through_8_return_exactly_k_cards():
    base_profiles = [
        (0, 2, {"monthly_spend": 10, "data_consumption_gb": 2, "voice_minutes": 10, "clv": 5}),
        (1, 2, {"monthly_spend": 25, "data_consumption_gb": 20, "voice_minutes": 80, "clv": 50}),
        (2, 2, {"monthly_spend": 45, "data_consumption_gb": 40, "voice_minutes": 130, "clv": 120}),
        (3, 2, {"monthly_spend": 65, "data_consumption_gb": 65, "voice_minutes": 180, "clv": 220}),
        (4, 2, {"monthly_spend": 85, "data_consumption_gb": 85, "voice_minutes": 230, "clv": 400}),
        (5, 2, {"monthly_spend": 105, "data_consumption_gb": 100, "voice_minutes": 280, "clv": 650}),
        (6, 2, {"monthly_spend": 130, "data_consumption_gb": 120, "voice_minutes": 320, "clv": 900}),
        (7, 2, {"monthly_spend": 170, "data_consumption_gb": 150, "voice_minutes": 360, "clv": 1300}),
    ]

    for k in range(2, 9):
        result = segment_from_profiles(base_profiles[:k], k=k)
        assert len(result["clusters"]) == k
        assert len(result["business_segments"]) == k


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
