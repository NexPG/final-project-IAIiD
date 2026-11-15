"""CLI: Great Expectations validation for the processed dataset.

Use ``--dirty`` to run the same suite against a deliberately corrupted copy.
The dirty run is expected to fail and demonstrates that validation catches
schema, null, duplicate, label and length problems.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import great_expectations as gx
import pandas as pd

from music_support_triage.data.schema import LABEL_QUALITIES, LABELS, SOURCES, SPLITS


def build_suite() -> gx.ExpectationSuite:
    """Create the project's reusable expectation suite."""
    suite = gx.ExpectationSuite(name="music_support_triage_dataset")
    expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="text"),
        gx.expectations.ExpectColumnValuesToBeInSet(column="label", value_set=list(LABELS)),
        gx.expectations.ExpectColumnValuesToBeInSet(column="split", value_set=list(SPLITS)),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="label_quality", value_set=list(LABEL_QUALITIES)
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(column="source", value_set=list(SOURCES)),
        gx.expectations.ExpectColumnValuesToBeUnique(column="id"),
        gx.expectations.ExpectColumnValueLengthsToBeBetween(
            column="text", min_value=10, max_value=5000
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="channel", value_set=["twitter", "app", "web", "email", "chat"]
        ),
    ]
    for expectation in expectations:
        suite.add_expectation(expectation)
    return suite


def validate_frame(frame: pd.DataFrame) -> dict[str, object]:
    """Run the suite against a dataframe and return a JSON-ready report."""
    context = gx.get_context()
    data_source = context.data_sources.add_pandas("pandas")
    asset = data_source.add_dataframe_asset("dataset")
    batch_definition = asset.add_batch_definition_whole_dataframe("whole")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": frame})
    result = batch.validate(build_suite())
    failed = [
        {
            "expectation": item["expectation_config"]["type"],
            "column": item["expectation_config"]["kwargs"].get("column"),
            "observed": item["result"].get("observed_value"),
        }
        for item in result.results
        if not item["success"]
    ]
    return {
        "success": bool(result.success),
        "evaluated_expectations": len(result.results),
        "successful_expectations": len(result.results) - len(failed),
        "failed_expectations": failed,
        "rows": int(len(frame)),
    }


def make_dirty(frame: pd.DataFrame) -> pd.DataFrame:
    """Inject common data-quality failures into a copy."""
    dirty = frame.copy()
    dirty.loc[0, "text"] = ""
    dirty.loc[1, "label"] = "not_a_label"
    dirty.loc[2, "split"] = "wrong_split"
    dirty.loc[3, "id"] = dirty.loc[4, "id"]
    dirty.loc[5, "text"] = "short"
    return dirty


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed/dataset.csv"))
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--dirty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame = pd.read_csv(args.data)
    if args.dirty:
        frame = make_dirty(frame)
    report = validate_frame(frame)
    output = args.output or Path(
        "data/processed/ge_report_dirty.json" if args.dirty else "data/processed/ge_report.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.dirty:
        # Dirty data must be rejected.
        return 0 if not report["success"] else 1
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
