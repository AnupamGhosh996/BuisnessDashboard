import math
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional
from backend.app.services.data_loader import DataLoaderService

class ForecastingService:
    @staticmethod
    def generate_forecast(
        columns: list[str],
        rows: list[dict[str, Any]],
        metric_column: Optional[str] = None,
        date_column: Optional[str] = None,
        horizon_days: int = 30,
        method: str = "linear"
    ) -> dict[str, Any]:
        """Calculates time series forecast with confidence intervals and accuracy metrics."""
        mappings = DataLoaderService.map_columns(columns)

        target_date = date_column or mappings.get("date")
        target_metric = metric_column or mappings.get("revenue") or mappings.get("profit")

        if not target_metric or target_metric not in columns:
            for col in columns:
                vals = [r.get(col) for r in rows[:50]]
                if DataLoaderService.infer_type(vals) in ("integer", "float"):
                    target_metric = col
                    break

        if not target_date or not target_metric:
            raise ValueError("Dataset requires a date column and a numerical metric column to perform forecasting.")

        def parse_float(val: Any) -> float:
            if val is None or str(val).strip() == "":
                return 0.0
            try:
                return float(str(val).replace("$", "").replace(",", ""))
            except ValueError:
                return 0.0

        # Aggregate daily data chronologically
        daily_agg = defaultdict(float)
        date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"]

        for r in rows:
            raw_d = str(r.get(target_date, "")).strip().split()[0]
            val = parse_float(r.get(target_metric))
            # Try parse date
            parsed = None
            for fmt in date_formats:
                try:
                    parsed = datetime.strptime(raw_d, fmt)
                    break
                except ValueError:
                    continue
            if parsed:
                iso_d = parsed.strftime("%Y-%m-%d")
                daily_agg[iso_d] += val

        sorted_dates = sorted(daily_agg.keys())
        if len(sorted_dates) < 7:
            raise ValueError(f"Insufficient chronological data ({len(sorted_dates)} unique dates found, at least 7 required for reliable forecasting).")

        # Fill missing daily dates to form a contiguous sequence
        first_d = datetime.strptime(sorted_dates[0], "%Y-%m-%d")
        last_d = datetime.strptime(sorted_dates[-1], "%Y-%m-%d")
        total_days_span = (last_d - first_d).days + 1

        contiguous_history = []
        curr = first_d
        while curr <= last_d:
            d_key = curr.strftime("%Y-%m-%d")
            contiguous_history.append((d_key, daily_agg.get(d_key, 0.0)))
            curr += timedelta(days=1)

        y_vals = [val for _, val in contiguous_history]
        N = len(y_vals)

        # 1. Linear Trend Regression: y = a + b * x
        x_indices = list(range(N))
        mean_x = statistics.mean(x_indices)
        mean_y = statistics.mean(y_vals)

        numer = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_indices, y_vals))
        denom = sum((x - mean_x) ** 2 for x in x_indices)
        slope = numer / denom if denom != 0 else 0.0
        intercept = mean_y - slope * mean_x

        # Calculate historical residuals for accuracy & confidence bounds
        residuals = []
        fitted_vals = []
        for x, actual in zip(x_indices, y_vals):
            pred = max(0.0, intercept + slope * x)
            fitted_vals.append(pred)
            residuals.append(actual - pred)

        mae = statistics.mean(abs(r) for r in residuals)
        rmse = math.sqrt(statistics.mean(r ** 2 for r in residuals))
        valid_actuals = [a for a in y_vals if a > 0]
        mape = (
            statistics.mean(abs(r) / a for r, a in zip(residuals, y_vals) if a > 0) * 100
            if valid_actuals else 15.0
        )
        residual_std = statistics.stdev(residuals) if len(residuals) > 1 else mae

        # 2. Moving Average / Exponential Smoothing values if chosen
        alpha = 0.3
        beta = 0.1
        exp_level = y_vals[0]
        exp_trend = (y_vals[-1] - y_vals[0]) / N if N > 1 else 0.0

        for y in y_vals:
            prev_level = exp_level
            exp_level = alpha * y + (1 - alpha) * (exp_level + exp_trend)
            exp_trend = beta * (exp_level - prev_level) + (1 - beta) * exp_trend

        # Trend Direction
        if slope > 0.05 * (mean_y / max(1, N)):
            trend_direction = "Upward Growth"
        elif slope < -0.05 * (mean_y / max(1, N)):
            trend_direction = "Downward Trend"
        else:
            trend_direction = "Stable"

        # Generate future forecast points
        forecast_points = []

        # Downsample historical points for smooth visualization (up to 60 historical points)
        hist_step = max(1, N // 60)
        for idx in range(0, N, hist_step):
            d_str, val = contiguous_history[idx]
            forecast_points.append({
                "date": d_str,
                "historical_value": round(val, 2),
                "forecast_value": None,
                "lower_bound": None,
                "upper_bound": None
            })

        # Future forecast points
        last_date_obj = last_d
        # Limit horizon steps to max 60 points for charting
        forecast_step = max(1, horizon_days // 30)

        for day_offset in range(1, horizon_days + 1, forecast_step):
            future_d = last_date_obj + timedelta(days=day_offset)
            d_str = future_d.strftime("%Y-%m-%d")
            future_x = N + day_offset

            if method == "moving_average":
                window = min(14, len(y_vals))
                fc_val = statistics.mean(y_vals[-window:]) + slope * day_offset * 0.5
            elif method == "exponential_smoothing":
                fc_val = exp_level + day_offset * exp_trend
            else:  # linear
                fc_val = intercept + slope * future_x

            fc_val = max(0.0, fc_val)

            # Expanding confidence bounds (95% approx: 1.96 * std * sqrt(1 + day/N))
            spread = 1.96 * residual_std * math.sqrt(1 + (day_offset / max(1, N)))
            lower_b = max(0.0, fc_val - spread)
            upper_b = fc_val + spread

            forecast_points.append({
                "date": d_str,
                "historical_value": None,
                "forecast_value": round(fc_val, 2),
                "lower_bound": round(lower_b, 2),
                "upper_bound": round(upper_b, 2)
            })

        return {
            "dataset_id": 0,
            "metric": target_metric,
            "date_column": target_date,
            "horizon_days": horizon_days,
            "method": method,
            "trend_direction": trend_direction,
            "accuracy": {
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "mape": round(min(99.9, mape), 1)
            },
            "points": forecast_points,
            "historical_count": N,
            "forecast_count": len([p for p in forecast_points if p["forecast_value"] is not None]),
            "disclaimer": "Forecasts are algorithmic estimates based on historical trajectories and should be evaluated alongside market domain conditions."
        }
