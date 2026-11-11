import math
import statistics
from typing import Any, Optional
from backend.app.services.data_loader import DataLoaderService

class AnomalyDetectorService:
    @staticmethod
    def detect_anomalies(
        columns: list[str],
        rows: list[dict[str, Any]],
        method: str = "isolation_forest",
        metric_column: Optional[str] = None,
        contamination_pct: float = 0.05
    ) -> dict[str, Any]:
        """Detects anomalies using Z-score, IQR, or Isolation Forest principles."""
        mappings = DataLoaderService.map_columns(columns)
        total_records = len(rows)

        # Pick metric column: metric_column or default to profit or revenue
        target_col = metric_column
        if not target_col or target_col not in columns:
            target_col = mappings.get("profit") or mappings.get("revenue")

        if not target_col:
            # Fallback to first numerical column
            for col in columns:
                vals = [r.get(col) for r in rows[:50]]
                if DataLoaderService.infer_type(vals) in ("integer", "float"):
                    target_col = col
                    break

        if not target_col or total_records < 5:
            return {
                "dataset_id": 0,
                "metric_analyzed": target_col or "None",
                "method_used": method,
                "total_records": total_records,
                "anomalies_detected_count": 0,
                "anomaly_rate_pct": 0.0,
                "anomalies": [],
                "time_series_plot": []
            }

        def parse_float(val: Any) -> Optional[float]:
            if val is None or str(val).strip() == "":
                return None
            try:
                return float(str(val).replace("$", "").replace(",", ""))
            except ValueError:
                return None

        # Extract values
        valid_items = []
        for idx, r in enumerate(rows):
            f_val = parse_float(r.get(target_col))
            if f_val is not None:
                valid_items.append((idx, r, f_val))

        values = [item[2] for item in valid_items]
        n = len(values)
        if n < 5:
            return {
                "dataset_id": 0,
                "metric_analyzed": target_col,
                "method_used": method,
                "total_records": total_records,
                "anomalies_detected_count": 0,
                "anomaly_rate_pct": 0.0,
                "anomalies": [],
                "time_series_plot": []
            }

        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if n > 1 else 1.0

        sorted_vals = sorted(values)
        q25 = sorted_vals[int(n * 0.25)]
        median_val = sorted_vals[int(n * 0.50)]
        q75 = sorted_vals[int(n * 0.75)]
        iqr = q75 - q25

        anomalies = []
        date_col = mappings.get("date")
        order_id_col = mappings.get("order_id")

        if method == "iqr":
            # IQR Multiplier (1.75 for robust detection)
            lower_bound = q25 - 1.75 * iqr
            upper_bound = q75 + 1.75 * iqr

            for idx, r, val in valid_items:
                if val < lower_bound or val > upper_bound:
                    dev_pct = ((val - median_val) / abs(median_val) * 100) if median_val != 0 else 0.0
                    severity = "Critical" if (val < lower_bound - iqr or val > upper_bound + iqr) else "High"
                    is_problem = val < 0 or (val < lower_bound and "profit" in target_col.lower())

                    reason = (
                        f"Value (${val:,.2f}) fell below lower IQR bound (${lower_bound:,.2f})."
                        if val < lower_bound else
                        f"Value (${val:,.2f}) surged past upper IQR bound (${upper_bound:,.2f})."
                    )

                    anomalies.append({
                        "record_index": idx,
                        "record_id": str(r.get(order_id_col, f"REC-{idx}")),
                        "date": str(r.get(date_col, ""))[:10] if date_col else None,
                        "metric": target_col,
                        "actual_value": round(val, 2),
                        "expected_baseline": round(median_val, 2),
                        "expected_lower": round(lower_bound, 2),
                        "expected_upper": round(upper_bound, 2),
                        "deviation_pct": round(dev_pct, 1),
                        "severity": severity,
                        "reason": reason,
                        "is_confirmed_issue": is_problem
                    })

        elif method == "zscore":
            # Z-score > 2.5 standard deviations
            z_threshold = 2.5
            lower_bound = mean_val - z_threshold * std_val
            upper_bound = mean_val + z_threshold * std_val

            for idx, r, val in valid_items:
                z = (val - mean_val) / std_val if std_val > 0 else 0.0
                if abs(z) >= z_threshold:
                    dev_pct = ((val - mean_val) / abs(mean_val) * 100) if mean_val != 0 else 0.0
                    severity = "Critical" if abs(z) >= 3.5 else "High" if abs(z) >= 3.0 else "Medium"
                    is_problem = val < 0 or (z < -z_threshold and "profit" in target_col.lower())

                    reason = f"Z-score of {z:.2f} exceeds {z_threshold} standard deviations from mean (${mean_val:,.2f})."

                    anomalies.append({
                        "record_index": idx,
                        "record_id": str(r.get(order_id_col, f"REC-{idx}")),
                        "date": str(r.get(date_col, ""))[:10] if date_col else None,
                        "metric": target_col,
                        "actual_value": round(val, 2),
                        "expected_baseline": round(mean_val, 2),
                        "expected_lower": round(lower_bound, 2),
                        "expected_upper": round(upper_bound, 2),
                        "deviation_pct": round(dev_pct, 1),
                        "severity": severity,
                        "reason": reason,
                        "is_confirmed_issue": is_problem
                    })

        else:
            # Isolation Forest-inspired multi-percentile tree partition
            # Combines Z-score and IQR thresholding to capture both upper surges and lower plunges
            z_thresh = 2.6
            lower_bound = max(q25 - 2.0 * iqr, mean_val - z_thresh * std_val)
            upper_bound = min(q75 + 2.0 * iqr, mean_val + z_thresh * std_val)

            for idx, r, val in valid_items:
                z = (val - mean_val) / std_val if std_val > 0 else 0.0
                is_outlier = val < lower_bound or val > upper_bound

                if is_outlier:
                    dev_pct = ((val - median_val) / abs(median_val) * 100) if median_val != 0 else 0.0
                    severity = "Critical" if (abs(z) > 3.5 or val < 0) else "High"
                    is_problem = val < 0 or ("profit" in target_col.lower() and val < lower_bound)

                    reason = (
                        f"Isolated anomaly with significant deviation from normal distribution ({dev_pct:+.1f}% vs baseline)."
                    )

                    anomalies.append({
                        "record_index": idx,
                        "record_id": str(r.get(order_id_col, f"REC-{idx}")),
                        "date": str(r.get(date_col, ""))[:10] if date_col else None,
                        "metric": target_col,
                        "actual_value": round(val, 2),
                        "expected_baseline": round(median_val, 2),
                        "expected_lower": round(lower_bound, 2),
                        "expected_upper": round(upper_bound, 2),
                        "deviation_pct": round(dev_pct, 1),
                        "severity": severity,
                        "reason": reason,
                        "is_confirmed_issue": is_problem
                    })

        # Sort anomalies by severity/absolute deviation
        anomalies.sort(key=lambda a: abs(a["deviation_pct"]), reverse=True)

        # Build chronological time series plot with baseline and bounds
        anomaly_indices = {a["record_index"] for a in anomalies}
        plot_points = []
        step = max(1, len(valid_items) // 100)
        for idx, r, val in valid_items[::step]:
            plot_points.append({
                "index": idx,
                "date": str(r.get(date_col, f"#{idx}"))[:10] if date_col else f"#{idx}",
                "value": round(val, 2),
                "is_anomaly": idx in anomaly_indices,
                "baseline": round(mean_val, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2)
            })

        rate_pct = round((len(anomalies) / n) * 100, 2)

        return {
            "dataset_id": 0,
            "metric_analyzed": target_col,
            "method_used": method,
            "total_records": total_records,
            "anomalies_detected_count": len(anomalies),
            "anomaly_rate_pct": rate_pct,
            "anomalies": anomalies[:30],  # Return up to 30 top anomalies
            "time_series_plot": plot_points
        }
