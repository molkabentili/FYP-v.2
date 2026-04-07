from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline import DataPreprocessor


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SmartSeg Sprint 2 preprocessing pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument(
        "--output-json",
        default="preprocessing_result.json",
        help="Path to save preprocessing JSON result",
    )
    parser.add_argument(
        "--output-cleaned-csv",
        default="",
        help="Optional path to save cleaned numeric feature dataset",
    )
    args = parser.parse_args()

    engine = DataPreprocessor()

    inspect_result = engine.inspect_from_csv(args.input)
    preprocess_result = engine.preprocess_from_csv(args.input)

    payload = {
        "inspect": inspect_result,
        "preprocess": preprocess_result,
    }

    output_json_path = Path(args.output_json).resolve()
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with output_json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved preprocessing JSON to: {output_json_path}")
    print(json.dumps(preprocess_result["cleaned_shape"], indent=2))

    if args.output_cleaned_csv.strip():
        cleaned = engine.build_cleaned_feature_frame_from_csv(args.input)

        output_csv_path = Path(args.output_cleaned_csv).resolve()
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(output_csv_path, index=False)
        print(f"Saved cleaned CSV to: {output_csv_path}")


if __name__ == "__main__":
    main()
