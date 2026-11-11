import os
import csv
import json
import re
from datetime import datetime
from typing import Any, Optional

class DataLoaderService:
    @staticmethod
    def detect_encoding(file_path: str) -> str:
        for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    f.read(4096)
                return enc
            except UnicodeDecodeError:
                continue
        return "utf-8"

    @staticmethod
    def load_records(file_path: str) -> tuple[list[str], list[dict[str, Any]]]:
        """Loads records from a CSV file, returning (columns, rows)."""
        enc = DataLoaderService.detect_encoding(file_path)
        with open(file_path, "r", encoding=enc, newline="") as f:
            # Check delimiter
            sample = f.read(4096)
            f.seek(0)
            delimiter = ","
            if sample.count(";") > sample.count(","):
                delimiter = ";"
            elif sample.count("\t") > sample.count(","):
                delimiter = "\t"

            reader = csv.DictReader(f, delimiter=delimiter)
            columns = [c.strip() for c in (reader.fieldnames or [])]
            rows = []
            for r in reader:
                clean_row = {}
                for k, v in r.items():
                    key = k.strip() if k else ""
                    clean_row[key] = v.strip() if isinstance(v, str) else v
                rows.append(clean_row)
        return columns, rows

    @staticmethod
    def infer_type(values: list[Any]) -> str:
        """Infers the data type of a column based on its sample values."""
        non_empty = [v for v in values if v is not None and str(v).strip() != ""]
        if not non_empty:
            return "string"

        # Check numeric (integer / float)
        num_count = 0
        int_count = 0
        date_count = 0

        date_formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y",
            "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"
        ]

        for val in non_empty[:100]:
            s = str(val).strip().replace("$", "").replace(",", "")
            # Check float/int
            try:
                f_val = float(s)
                num_count += 1
                if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
                    int_count += 1
                continue
            except ValueError:
                pass

            # Check date
            for df in date_formats:
                try:
                    datetime.strptime(s.split(".")[0], df)
                    date_count += 1
                    break
                except ValueError:
                    continue

        sample_len = min(len(non_empty), 100)
        if num_count / sample_len > 0.8:
            return "integer" if (int_count / sample_len > 0.8) else "float"
        if date_count / sample_len > 0.8:
            return "datetime"
        
        # Check boolean
        bool_vals = {"true", "false", "yes", "no", "1", "0", "t", "f"}
        if all(str(v).lower() in bool_vals for v in non_empty[:50]):
            return "boolean"

        return "string"

    @staticmethod
    def map_columns(columns: list[str]) -> dict[str, str]:
        """Automatically maps business concepts to column names."""
        mapping_rules = {
            "revenue": ["revenue", "sales", "turnover", "gross_sales", "total_amount", "amount"],
            "profit": ["profit", "net_profit", "earnings", "net_income", "margin"],
            "cost": ["cost", "cogs", "expenses", "expenditure", "total_cost"],
            "quantity": ["quantity", "qty", "volume", "units", "count"],
            "order_id": ["order_id", "order id", "orderid", "invoice_id", "invoice id", "transaction_id"],
            "date": ["order_date", "order date", "date", "timestamp", "transaction_date", "sale_date"],
            "product": ["product", "product_name", "product name", "item", "item_name", "sku"],
            "category": ["category", "product_category", "department", "segment", "type"],
            "region": ["region", "country", "territory", "state", "location", "area", "market"],
            "customer": ["customer_id", "customer id", "customer", "customer_name", "client_id"]
        }

        detected = {}
        used_cols = set()

        for role, patterns in mapping_rules.items():
            for col in columns:
                if col in used_cols:
                    continue
                clean_name = re.sub(r"[_\-\s]+", " ", col.lower()).strip()
                for pattern in patterns:
                    if clean_name == pattern or clean_name == pattern.replace("_", " "):
                        detected[role] = col
                        used_cols.add(col)
                        break
                if role in detected:
                    break

        return detected

    @staticmethod
    def get_preview(
        columns: list[str],
        rows: list[dict[str, Any]],
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> dict[str, Any]:
        """Returns paginated, searchable, sorted preview data."""
        # Calculate column metadata
        col_types = {}
        missing_counts = {}
        unique_counts = {}
        sample_values = {}

        for col in columns:
            vals = [r.get(col) for r in rows]
            col_types[col] = DataLoaderService.infer_type(vals)
            missing = sum(1 for v in vals if v is None or str(v).strip() == "")
            missing_counts[col] = missing
            clean_vals = [v for v in vals if v is not None and str(v).strip() != ""]
            unique_counts[col] = len(set(clean_vals))
            sample_values[col] = list(dict.fromkeys(clean_vals[:10]))

        # Check duplicates
        seen = set()
        duplicate_count = 0
        for r in rows:
            # Tuple of values as row hash
            row_hash = tuple(sorted((k, str(v)) for k, v in r.items()))
            if row_hash in seen:
                duplicate_count += 1
            else:
                seen.add(row_hash)

        # Filter by search
        filtered_rows = rows
        if search:
            s_lower = search.lower()
            filtered_rows = [
                r for r in rows
                if any(s_lower in str(v).lower() for v in r.values() if v is not None)
            ]

        # Sort
        if sort_by and sort_by in columns:
            is_num = col_types.get(sort_by) in ("integer", "float")
            def sort_key(row):
                v = row.get(sort_by)
                if v is None or str(v).strip() == "":
                    return float("-inf") if sort_order == "desc" else float("inf")
                if is_num:
                    try:
                        return float(str(v).replace("$", "").replace(",", ""))
                    except ValueError:
                        return float("-inf")
                return str(v).lower()

            filtered_rows.sort(key=sort_key, reverse=(sort_order == "desc"))

        # Paginate
        total_filtered = len(filtered_rows)
        total_pages = max(1, (total_filtered + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        paged_rows = filtered_rows[start_idx : start_idx + page_size]

        column_info = []
        role_mappings = DataLoaderService.map_columns(columns)
        rev_mappings = {v: k for k, v in role_mappings.items()}

        for col in columns:
            column_info.append({
                "name": col,
                "data_type": col_types.get(col, "string"),
                "missing_count": missing_counts.get(col, 0),
                "unique_count": unique_counts.get(col, 0),
                "sample_values": sample_values.get(col, []),
                "role_mapping": rev_mappings.get(col)
            })

        return {
            "total_rows": len(rows),
            "total_columns": len(columns),
            "column_info": column_info,
            "missing_values_total": sum(missing_counts.values()),
            "duplicate_rows_count": duplicate_count,
            "detected_mappings": role_mappings,
            "sample_rows": paged_rows,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "filtered_count": total_filtered
        }
