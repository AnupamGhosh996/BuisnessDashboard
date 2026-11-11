import math
import statistics
from datetime import datetime
from typing import Any, Optional
from backend.app.services.data_loader import DataLoaderService

class DataCleanerService:
    @staticmethod
    def inspect_dataset(columns: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
        """Detects data quality issues: missing, duplicates, outliers, types."""
        total_rows = len(rows)
        issues = []
        suggestions = []

        # 1. Duplicate detection
        seen = set()
        duplicates = 0
        for r in rows:
            row_hash = tuple(sorted((k, str(v)) for k, v in r.items()))
            if row_hash in seen:
                duplicates += 1
            else:
                seen.add(row_hash)

        if duplicates > 0:
            issues.append({
                "issue_type": "duplicate_rows",
                "column": None,
                "affected_count": duplicates,
                "description": f"Found {duplicates} completely duplicate row(s).",
                "suggested_action": "Remove duplicate rows to prevent skewed aggregations."
            })
            suggestions.append(f"Remove {duplicates} duplicate rows.")

        # 2. Missing values & Outlier detection
        missing_by_col = {}
        outliers_by_col = {}

        for col in columns:
            vals = [r.get(col) for r in rows]
            col_type = DataLoaderService.infer_type(vals)

            missing_count = sum(1 for v in vals if v is None or str(v).strip() == "")
            if missing_count > 0:
                missing_by_col[col] = missing_count
                pct = (missing_count / total_rows) * 100
                issues.append({
                    "issue_type": "missing_values",
                    "column": col,
                    "affected_count": missing_count,
                    "description": f"Column '{col}' has {missing_count} missing value(s) ({pct:.1f}%).",
                    "suggested_action": f"Impute with {'mean/median' if col_type in ('integer', 'float') else 'mode'} or drop empty rows."
                })
                suggestions.append(f"Impute {missing_count} missing values in '{col}'.")

            # Outliers for numerical columns
            if col_type in ("integer", "float"):
                num_vals = []
                for v in vals:
                    if v is not None and str(v).strip() != "":
                        try:
                            num_vals.append(float(str(v).replace("$", "").replace(",", "")))
                        except ValueError:
                            pass

                if len(num_vals) >= 10:
                    sorted_vals = sorted(num_vals)
                    q25 = sorted_vals[int(len(sorted_vals) * 0.25)]
                    q75 = sorted_vals[int(len(sorted_vals) * 0.75)]
                    iqr = q75 - q25
                    lower_bound = q25 - 1.5 * iqr
                    upper_bound = q75 + 1.5 * iqr

                    outlier_count = sum(1 for x in num_vals if x < lower_bound or x > upper_bound)
                    if outlier_count > 0:
                        outliers_by_col[col] = outlier_count
                        issues.append({
                            "issue_type": "outliers",
                            "column": col,
                            "affected_count": outlier_count,
                            "description": f"Column '{col}' has {outlier_count} statistical outlier(s) outside IQR [{lower_bound:.2f}, {upper_bound:.2f}].",
                            "suggested_action": "Review outlier distribution in Anomaly Detection or normalize."
                        })
                        suggestions.append(f"Examine {outlier_count} statistical outliers in '{col}'.")

        if not suggestions:
            suggestions.append("Dataset appears clean and ready for analysis.")

        return {
            "total_rows": total_rows,
            "duplicate_rows": duplicates,
            "missing_values_by_column": missing_by_col,
            "outliers_by_column": outliers_by_col,
            "issues": issues,
            "cleaning_suggestions": suggestions
        }

    @staticmethod
    def apply_cleaning(
        columns: list[str],
        rows: list[dict[str, Any]],
        remove_duplicates: bool = True,
        fill_numerical: Optional[str] = "mean",
        fill_categorical: Optional[str] = "mode",
        drop_missing_rows: bool = False,
        normalize_columns: Optional[list[str]] = None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Applies data cleaning and returns (cleaned_rows, summary_stats)."""
        initial_count = len(rows)
        duplicates_removed = 0
        missing_imputed = 0
        summary_notes = []

        working_rows = [dict(r) for r in rows]

        # 1. Remove duplicate rows
        if remove_duplicates:
            unique_rows = []
            seen = set()
            for r in working_rows:
                row_hash = tuple(sorted((k, str(v)) for k, v in r.items()))
                if row_hash not in seen:
                    seen.add(row_hash)
                    unique_rows.append(r)
                else:
                    duplicates_removed += 1
            working_rows = unique_rows
            if duplicates_removed > 0:
                summary_notes.append(f"Removed {duplicates_removed} duplicate row(s).")

        # 2. Drop missing rows if requested
        if drop_missing_rows:
            before_drop = len(working_rows)
            working_rows = [
                r for r in working_rows
                if all(r.get(c) is not None and str(r.get(c)).strip() != "" for c in columns)
            ]
            dropped = before_drop - len(working_rows)
            if dropped > 0:
                summary_notes.append(f"Dropped {dropped} row(s) containing missing values.")

        # 3. Impute missing numerical and categorical
        col_types = {col: DataLoaderService.infer_type([r.get(col) for r in working_rows]) for col in columns}

        for col in columns:
            ctype = col_types[col]
            vals = [r.get(col) for r in working_rows]

            if ctype in ("integer", "float") and fill_numerical in ("mean", "median"):
                num_vals = []
                for v in vals:
                    if v is not None and str(v).strip() != "":
                        try:
                            num_vals.append(float(str(v).replace("$", "").replace(",", "")))
                        except ValueError:
                            pass

                if num_vals:
                    replacement = statistics.mean(num_vals) if fill_numerical == "mean" else statistics.median(num_vals)
                    if ctype == "integer":
                        replacement = int(round(replacement))
                    else:
                        replacement = round(replacement, 2)

                    col_imputed = 0
                    for r in working_rows:
                        val = r.get(col)
                        if val is None or str(val).strip() == "":
                            r[col] = replacement
                            col_imputed += 1

                    if col_imputed > 0:
                        missing_imputed += col_imputed
                        summary_notes.append(f"Imputed {col_imputed} missing value(s) in '{col}' using {fill_numerical} ({replacement}).")

            elif ctype == "string" and fill_categorical == "mode":
                str_vals = [str(v).strip() for v in vals if v is not None and str(v).strip() != ""]
                if str_vals:
                    mode_val = statistics.mode(str_vals)
                    col_imputed = 0
                    for r in working_rows:
                        val = r.get(col)
                        if val is None or str(val).strip() == "":
                            r[col] = mode_val
                            col_imputed += 1

                    if col_imputed > 0:
                        missing_imputed += col_imputed
                        summary_notes.append(f"Imputed {col_imputed} missing categorical value(s) in '{col}' using mode ('{mode_val}').")

        # 4. Normalize numerical columns if requested
        if normalize_columns:
            for col in normalize_columns:
                if col in columns and col_types.get(col) in ("integer", "float"):
                    num_vals = []
                    for r in working_rows:
                        try:
                            num_vals.append(float(str(r.get(col, 0)).replace("$", "").replace(",", "")))
                        except ValueError:
                            num_vals.append(0.0)

                    if num_vals:
                        min_v = min(num_vals)
                        max_v = max(num_vals)
                        rng = max_v - min_v if max_v != min_v else 1.0

                        for idx, r in enumerate(working_rows):
                            norm_val = round((num_vals[idx] - min_v) / rng, 4)
                            r[f"{col}_normalized"] = norm_val

                        summary_notes.append(f"Created normalized feature '{col}_normalized' (Min-Max 0 to 1).")

        final_count = len(working_rows)

        summary = {
            "rows_before": initial_count,
            "rows_after": final_count,
            "duplicates_removed": duplicates_removed,
            "missing_imputed_count": missing_imputed,
            "summary_notes": summary_notes
        }

        return working_rows, summary
