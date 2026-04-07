from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _yes_no_to_int(series: pd.Series) -> pd.Series:
    return series.fillna("No").astype(str).str.strip().str.lower().eq("yes").astype(int)


def _safe_numeric(value) -> pd.Series:
    """Convert value to numeric Series if it's a Series, otherwise create Series."""
    if isinstance(value, pd.Series):
        return pd.to_numeric(value, errors="coerce")
    return pd.Series(value)


def engineer_telco_features(df: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering for telco datasets."""
    engineered = df.copy()

    if "TotalCharges" in engineered.columns:
        engineered["TotalCharges"] = _safe_numeric(engineered["TotalCharges"])

    tenure = _safe_numeric(engineered["tenure"]) if "tenure" in engineered.columns else pd.Series(0, index=engineered.index)
    tenure = tenure.fillna(0)
    
    monthly = _safe_numeric(engineered["MonthlyCharges"]) if "MonthlyCharges" in engineered.columns else pd.Series(0, index=engineered.index)
    monthly = monthly.fillna(0)
    
    total = _safe_numeric(engineered["TotalCharges"]) if "TotalCharges" in engineered.columns else pd.Series(0, index=engineered.index)
    total = total.fillna(0)

    engineered["estimated_usage_score"] = (monthly * 0.6 + total.div(tenure + 1) * 0.4).round(3)
    engineered["customer_activity_score"] = (tenure * 0.5 + monthly * 0.5).round(3)
    engineered["spending_level"] = pd.qcut(
        monthly.rank(method="first"),
        q=4,
        labels=["Low", "Medium", "High", "Very High"],
    ).astype(str)

    service_columns = [
        "PhoneService",
        "MultipleLines",
        "OnlineSecurity",
        "OnlineBackup",
        "DeviceProtection",
        "TechSupport",
        "StreamingTV",
        "StreamingMovies",
    ]
    existing_service_columns = [col for col in service_columns if col in engineered.columns]
    if existing_service_columns:
        service_count = sum(_yes_no_to_int(engineered[col]) for col in existing_service_columns)
    else:
        service_count = pd.Series(0, index=engineered.index)

    partner = _yes_no_to_int(engineered.get("Partner", pd.Series("No", index=engineered.index)))
    dependents = _yes_no_to_int(engineered.get("Dependents", pd.Series("No", index=engineered.index)))
    paperless = _yes_no_to_int(engineered.get("PaperlessBilling", pd.Series("No", index=engineered.index)))

    contract_map = {"month-to-month": 0, "one year": 1, "two year": 2}
    contract_score = (
        engineered.get("Contract", pd.Series("month-to-month", index=engineered.index))
        .astype(str)
        .str.strip()
        .str.lower()
        .map(contract_map)
        .fillna(0)
    )

    payment_series = engineered.get("PaymentMethod", pd.Series("", index=engineered.index)).astype(str).str.lower()
    auto_payment_flag = payment_series.str.contains("automatic").astype(int)

    internet_fiber_flag = (
        engineered.get("InternetService", pd.Series("", index=engineered.index))
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("fiber optic")
        .astype(int)
    )

    tech_support_no = (
        engineered.get("TechSupport", pd.Series("No", index=engineered.index))
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("no")
        .astype(int)
    )

    churn_numeric = (
        engineered.get("Churn", pd.Series("No", index=engineered.index))
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("yes")
        .astype(int)
    )

    engineered["engagement_score"] = (service_count * 1.4 + partner + dependents + contract_score).round(3)
    engineered["contract_security_score"] = contract_score
    engineered["digital_payment_score"] = (paperless + auto_payment_flag).astype(int)
    engineered["risk_signal_score"] = (
        internet_fiber_flag * 0.4 +
        tech_support_no * 0.3 +
        (contract_score == 0).astype(int) * 0.3
    ).round(3)
    engineered["observed_churn_flag"] = churn_numeric

    return engineered


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate engineered features for datasets")
    parser.add_argument("--input", default="data/real/telco_churn.csv", help="Path to input CSV")
    parser.add_argument(
        "--output",
        default="data/real/telco_churn_engineered.csv",
        help="Path to save engineered dataset",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    df = pd.read_csv(input_path)
    
    # Check if this is a telco dataset
    is_telco = all(col in df.columns for col in ["tenure", "MonthlyCharges", "Churn"])
    
    if is_telco:
        engineered = engineer_telco_features(df)
    else:
        # For non-telco datasets, create generic features from numeric columns
        engineered = df.copy()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            # Create generic features from numeric data
            for i, col in enumerate(numeric_cols[:3]):  # Use first 3 numeric cols
                if i < len(numeric_cols):
                    engineered[f"feature_scaled_{i}"] = (df[col] - df[col].mean()) / (df[col].std() + 1e-5)
            
            # Create an engagement score from numeric features
            if numeric_cols:
                engineered["engagement_score"] = df[numeric_cols].mean(axis=1).round(3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    engineered.to_csv(output_path, index=False)

    print(f"Saved engineered dataset to: {output_path}")
    print(f"Rows: {engineered.shape[0]}, Columns: {engineered.shape[1]}")


if __name__ == "__main__":
    main()
