import math
import statistics
from collections import Counter
from typing import Any
from backend.app.services.data_loader import DataLoaderService

class EDAEngineService:
    @staticmethod
    def calculate_eda(columns: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
        """Performs statistical EDA on the dataset."""
        numerical_stats = []
        categorical_stats = []
        num_column_data = {}

        total_rows = len(rows)
        if total_rows == 0:
            return {
                "numerical_stats": [],
                "categorical_stats": [],
                "correlation_matrix": {"columns": [], "matrix": []},
                "auto_summary": "Dataset is empty."
            }

        col_types = {col: DataLoaderService.infer_type([r.get(col) for r in rows]) for col in columns}

        # 1. Numerical Statistics
        for col in columns:
            ctype = col_types[col]
            vals = [r.get(col) for r in rows]

            if ctype in ("integer", "float"):
                clean_nums = []
                for v in vals:
                    if v is not None and str(v).strip() != "":
                        try:
                            clean_nums.append(float(str(v).replace("$", "").replace(",", "")))
                        except ValueError:
                            pass

                if len(clean_nums) > 0:
                    num_column_data[col] = clean_nums
                    n = len(clean_nums)
                    mean_val = statistics.mean(clean_nums)
                    median_val = statistics.median(clean_nums)
                    try:
                        mode_val = statistics.mode(clean_nums)
                    except statistics.StatisticsError:
                        mode_val = None

                    std_val = statistics.stdev(clean_nums) if n > 1 else 0.0
                    var_val = statistics.variance(clean_nums) if n > 1 else 0.0
                    min_val = min(clean_nums)
                    max_val = max(clean_nums)

                    sorted_nums = sorted(clean_nums)
                    q25 = sorted_nums[int(n * 0.25)]
                    q75 = sorted_nums[int(n * 0.75)]
                    iqr = q75 - q25

                    # Skewness
                    skew = None
                    if n > 2 and std_val > 0:
                        m3 = sum((x - mean_val) ** 3 for x in clean_nums) / n
                        skew = round(m3 / (std_val ** 3), 3)

                    numerical_stats.append({
                        "column": col,
                        "count": n,
                        "mean": round(mean_val, 2),
                        "median": round(median_val, 2),
                        "mode": round(mode_val, 2) if mode_val is not None else None,
                        "std": round(std_val, 2),
                        "variance": round(var_val, 2),
                        "min": round(min_val, 2),
                        "max": round(max_val, 2),
                        "q25": round(q25, 2),
                        "q75": round(q75, 2),
                        "iqr": round(iqr, 2),
                        "skewness": skew
                    })

            elif ctype in ("string", "boolean"):
                clean_cats = [str(v).strip() for v in vals if v is not None and str(v).strip() != ""]
                if clean_cats:
                    counts = Counter(clean_cats)
                    total_cat = len(clean_cats)
                    top_val, top_count = counts.most_common(1)[0]

                    freq_list = [
                        {
                            "category": cat,
                            "count": count,
                            "percentage": round((count / total_cat) * 100, 1)
                        }
                        for cat, count in counts.most_common(10)
                    ]

                    categorical_stats.append({
                        "column": col,
                        "total_count": total_cat,
                        "unique_count": len(counts),
                        "top_value": top_val,
                        "frequencies": freq_list
                    })

        # 2. Pearson Correlation Matrix for numerical columns
        num_cols = list(num_column_data.keys())
        corr_matrix = []
        correlations_list = []

        for i, c1 in enumerate(num_cols):
            row_corr = []
            v1 = num_column_data[c1]
            n = min(len(v1), len(rows))
            for j, c2 in enumerate(num_cols):
                if i == j:
                    row_corr.append(1.0)
                else:
                    v2 = num_column_data[c2]
                    # Common paired items
                    pairs = [(a, b) for a, b in zip(v1[:n], v2[:n]) if a is not None and b is not None]
                    if len(pairs) > 1:
                        x = [p[0] for p in pairs]
                        y = [p[1] for p in pairs]
                        mean_x = statistics.mean(x)
                        mean_y = statistics.mean(y)
                        numer = sum((a - mean_x) * (b - mean_y) for a, b in pairs)
                        denom = math.sqrt(sum((a - mean_x) ** 2 for a in x) * sum((b - mean_y) ** 2 for b in y))
                        r = round(numer / denom, 3) if denom > 0 else 0.0
                    else:
                        r = 0.0
                    row_corr.append(r)
                    if i < j:
                        correlations_list.append((c1, c2, r))
            corr_matrix.append(row_corr)

        # 3. Auto-generated EDA Narrative supported by calculations
        narrative_parts = []
        narrative_parts.append(f"Analyzed {total_rows} total records across {len(columns)} attributes ({len(num_cols)} numerical, {len(categorical_stats)} categorical).")

        # Highlights from numerical columns
        mappings = DataLoaderService.map_columns(columns)
        rev_col = mappings.get("revenue")
        profit_col = mappings.get("profit")

        if rev_col and rev_col in num_column_data:
            tot_rev = sum(num_column_data[rev_col])
            avg_rev = statistics.mean(num_column_data[rev_col])
            narrative_parts.append(f"Total {rev_col} amounts to ${tot_rev:,.2f} with an average transaction value of ${avg_rev:,.2f}.")

        if profit_col and profit_col in num_column_data:
            tot_profit = sum(num_column_data[profit_col])
            if rev_col and rev_col in num_column_data and tot_rev > 0:
                overall_margin = (tot_profit / tot_rev) * 100
                narrative_parts.append(f"Overall profit generated is ${tot_profit:,.2f}, representing a cumulative margin of {overall_margin:.1f}%.")

        # Top Category highlight
        cat_col = mappings.get("category")
        if cat_col:
            cat_stat = next((cs for cs in categorical_stats if cs["column"] == cat_col), None)
            if cat_stat and cat_stat["frequencies"]:
                top_c = cat_stat["frequencies"][0]
                narrative_parts.append(f"The dominant segment in '{cat_col}' is '{top_c['category']}', accounting for {top_c['count']} orders ({top_c['percentage']}%).")

        # Significant correlations
        strong_pos = [c for c in correlations_list if c[2] >= 0.7]
        strong_neg = [c for c in correlations_list if c[2] <= -0.7]
        if strong_pos:
            c1, c2, r = strong_pos[0]
            narrative_parts.append(f"Strong positive linear correlation detected between '{c1}' and '{c2}' (r = {r:.2f}).")
        if strong_neg:
            c1, c2, r = strong_neg[0]
            narrative_parts.append(f"Notable negative correlation identified between '{c1}' and '{c2}' (r = {r:.2f}).")

        auto_summary = " ".join(narrative_parts)

        return {
            "numerical_stats": numerical_stats,
            "categorical_stats": categorical_stats,
            "correlation_matrix": {
                "columns": num_cols,
                "matrix": corr_matrix
            },
            "auto_summary": auto_summary
        }
