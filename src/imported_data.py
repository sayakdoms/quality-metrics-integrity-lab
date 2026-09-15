"""Strict validation and chart preparation for user-owned quality CSV data."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from typing import BinaryIO, TextIO

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = ("period", "reported_rate")
OPTIONAL_COLUMNS = ("actual_rate", "target_rate")
ALLOWED_COLUMNS = frozenset((*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS))
MAX_IMPORT_ROWS = 10_000

CSV_TEMPLATE = """period,actual_rate,reported_rate,target_rate
Period 1,0.023,0.023,0.010
Period 2,0.022,0.021,0.010
Period 3,0.021,0.020,0.010
"""


class CSVValidationError(ValueError):
    """Raised when an uploaded CSV does not meet the documented schema."""


@dataclass(frozen=True)
class ImportedQualityData:
    """Validated imported data and the optional-series flags used by the UI."""

    frame: pd.DataFrame
    has_actual_rate: bool
    has_target_rate: bool

    @property
    def can_compute_reporting_gap(self) -> bool:
        return self.has_actual_rate


def _read_text(source: bytes | str | BinaryIO | TextIO) -> str:
    if isinstance(source, bytes):
        try:
            return source.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError as exc:
            raise CSVValidationError("CSV files must use UTF-8 text encoding.") from exc
    if isinstance(source, str):
        return source
    payload = source.read()
    return _read_text(payload)


def validate_quality_csv(source: bytes | str | BinaryIO | TextIO) -> ImportedQualityData:
    """Parse and strictly validate the supported CSV schema without repairing data."""
    text = _read_text(source)
    if not text.strip():
        raise CSVValidationError("The uploaded CSV is empty.")

    try:
        rows = csv.reader(StringIO(text))
        header = next(rows)
    except (csv.Error, StopIteration) as exc:
        raise CSVValidationError("The uploaded file is not a readable CSV.") from exc
    if len(header) != len(set(header)):
        raise CSVValidationError("CSV column names must be unique.")
    missing = sorted(set(REQUIRED_COLUMNS) - set(header))
    unknown = sorted(set(header) - ALLOWED_COLUMNS)
    if missing:
        raise CSVValidationError(f"Missing required column(s): {', '.join(missing)}.")
    if unknown:
        raise CSVValidationError(f"Unsupported column(s): {', '.join(unknown)}.")

    try:
        frame = pd.read_csv(StringIO(text), dtype={"period": "string"})
    except (pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as exc:
        raise CSVValidationError(f"The CSV could not be parsed: {exc}") from exc
    if frame.empty:
        raise CSVValidationError("The CSV must contain at least one data row.")
    if len(frame) > MAX_IMPORT_ROWS:
        raise CSVValidationError(
            f"The CSV contains more than the {MAX_IMPORT_ROWS:,}-row session limit."
        )
    if frame["period"].isna().any() or (frame["period"].str.strip() == "").any():
        raise CSVValidationError("Every row must contain a non-empty period value.")
    if frame["period"].duplicated().any():
        raise CSVValidationError("Period values must be unique and remain in source order.")

    rate_columns = [column for column in frame.columns if column.endswith("_rate")]
    for column in rate_columns:
        try:
            numeric = pd.to_numeric(frame[column], errors="raise").astype(float)
        except (TypeError, ValueError) as exc:
            raise CSVValidationError(f"Column '{column}' must contain only numbers.") from exc
        if numeric.isna().any() or not np.isfinite(numeric.to_numpy()).all():
            raise CSVValidationError(f"Column '{column}' cannot contain missing or infinite values.")
        if ((numeric < 0.0) | (numeric > 1.0)).any():
            raise CSVValidationError(
                f"Column '{column}' must use decimal fractions from 0 to 1 inclusive."
            )
        frame[column] = numeric

    return ImportedQualityData(
        frame=frame,
        has_actual_rate="actual_rate" in frame.columns,
        has_target_rate="target_rate" in frame.columns,
    )


def imported_chart_series(data: ImportedQualityData) -> pd.DataFrame:
    """Return long-form chart data while preserving the uploaded period order."""
    columns = ["reported_rate"]
    if data.has_actual_rate:
        columns.insert(0, "actual_rate")
    if data.has_target_rate:
        columns.append("target_rate")
    chart = data.frame[["period", *columns]].melt(
        id_vars="period", var_name="series", value_name="rate"
    )
    chart["series"] = chart["series"].map(
        {
            "actual_rate": "Actual defect rate",
            "reported_rate": "Reported defect rate",
            "target_rate": "Target reference",
        }
    )
    return chart


def imported_data_interpretation(data: ImportedQualityData) -> str:
    """Provide a descriptive statement that does not infer gaming or intent."""
    if not data.has_actual_rate:
        return (
            "Reporting-gap analysis cannot be computed because actual_rate was not "
            "provided as a comparison benchmark."
        )
    gap = data.frame["actual_rate"] - data.frame["reported_rate"]
    final_gap = float(gap.iloc[-1])
    return (
        f"The final uploaded observation has an actual-minus-reported gap of "
        f"{final_gap * 100:.2f} percentage points. This descriptive difference is not "
        "evidence of gaming or misconduct."
    )
