from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    missing_ratio_threshold: float = 0.4
    min_rows_for_clustering: int = 20
    min_features_for_clustering: int = 2
    k_min: int = 2
    k_max: int = 10
    random_state: int = 42
    n_init: int = 10


ID_LIKE_KEYWORDS = {
    "id",
    "customer_id",
    "customerid",
    "account_id",
    "accountid",
    "sim_number",
    "msisdn",
    "index",
    "uuid",
    "imei",
    "passport",
    "national_id",
}
