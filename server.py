import os
import sys
import json
import sqlite3
import cgi
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Set path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.config import settings, BASE_DIR
from backend.app.services.data_loader import DataLoaderService
from backend.app.services.data_cleaner import DataCleanerService
from backend.app.services.eda_engine import EDAEngineService
from backend.app.services.analytics_engine import AnalyticsEngineService
from backend.app.services.ai_analyst import AIAnalystService
from backend.app.services.anomaly_detector import AnomalyDetectorService
from backend.app.services.forecasting import ForecastingService
from backend.app.services.report_generator import ReportGeneratorService

DB_PATH = BASE_DIR / "insightiq.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            row_count INTEGER DEFAULT 0,
            column_count INTEGER DEFAULT 0,
            file_size_bytes INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0,
            is_cleaned INTEGER DEFAULT 0,
            parent_id INTEGER,
            metadata_json TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            query_plan_json TEXT,
            chart_recommendation_json TEXT,
            metrics_context_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_format TEXT DEFAULT 'pdf',
            summary_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Seed sample dataset if empty
    cursor.execute("SELECT COUNT(*) FROM datasets")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_path = settings.STORAGE_DATASETS_DIR / "sample_sales_dataset.csv"
        if sample_path.exists():
            cols, rows = DataLoaderService.load_records(str(sample_path))
            mappings = DataLoaderService.map_columns(cols)
            size = sample_path.stat().st_size
            meta = json.dumps({"columns": cols, "mappings": mappings})
            cursor.execute("""
                INSERT INTO datasets (filename, file_path, row_count, column_count, file_size_bytes, is_active, is_cleaned, metadata_json)
                VALUES (?, ?, ?, ?, ?, 1, 0, ?)
            """, ("sample_sales_dataset.csv", str(sample_path), len(rows), len(cols), size, meta))
            conn.commit()
            print(f"[InsightIQ Server] Seeded active sample dataset (805 rows).")

    conn.close()

init_db()

class InsightIQRequestHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, data, status_code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message, status_code=400):
        self._send_json({"detail": message, "status": "error"}, status_code)

    def _get_db(self):
        return sqlite3.connect(DB_PATH)

    def _get_active_dataset(self, conn, dataset_id=None):
        cursor = conn.cursor()
        if dataset_id:
            cursor.execute("SELECT id, filename, file_path, row_count, column_count, file_size_bytes, is_active, is_cleaned, parent_id, metadata_json, uploaded_at FROM datasets WHERE id = ?", (dataset_id,))
        else:
            cursor.execute("SELECT id, filename, file_path, row_count, column_count, file_size_bytes, is_active, is_cleaned, parent_id, metadata_json, uploaded_at FROM datasets WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            if not row:
                cursor.execute("SELECT id, filename, file_path, row_count, column_count, file_size_bytes, is_active, is_cleaned, parent_id, metadata_json, uploaded_at FROM datasets ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "filename": row[1],
            "file_path": row[2],
            "row_count": row[3],
            "column_count": row[4],
            "file_size_bytes": row[5],
            "is_active": bool(row[6]),
            "is_cleaned": bool(row[7]),
            "parent_id": row[8],
            "metadata_json": row[9],
            "uploaded_at": str(row[10])
        }

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Health
        if path == "/api/health":
            has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY))
            self._send_json({
                "status": "healthy",
                "app_name": "InsightIQ",
                "python_version": sys.version.split()[0],
                "database": "sqlite_connected",
                "ai_status": "ready" if has_anthropic else "deterministic_fallback (set ANTHROPIC_API_KEY for live Claude)",
                "datasets_storage": str(settings.STORAGE_DATASETS_DIR),
                "reports_storage": str(settings.STORAGE_REPORTS_DIR)
            })
            return

        # List Datasets
        if path == "/api/datasets":
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, filename, file_path, row_count, column_count, file_size_bytes, is_active, is_cleaned, parent_id, metadata_json, uploaded_at FROM datasets ORDER BY is_active DESC, id DESC")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                meta = json.loads(r[9] or "{}")
                results.append({
                    "id": r[0],
                    "filename": r[1],
                    "file_path": r[2],
                    "row_count": r[3],
                    "column_count": r[4],
                    "file_size_bytes": r[5],
                    "is_active": bool(r[6]),
                    "is_cleaned": bool(r[7]),
                    "parent_id": r[8],
                    "column_names": meta.get("columns", []),
                    "detected_mappings": meta.get("mappings", {}),
                    "uploaded_at": str(r[10])
                })
            conn.close()
            self._send_json(results)
            return

        # Dataset Preview /api/datasets/{id}
        if path.startswith("/api/datasets/"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            conn.close()
            if not ds or not os.path.exists(ds["file_path"]):
                self._send_error("Dataset not found", 404)
                return

            page = int(params.get("page", [1])[0])
            page_size = int(params.get("page_size", [25])[0])
            search = params.get("search", [None])[0]
            sort_by = params.get("sort_by", [None])[0]
            sort_order = params.get("sort_order", ["asc"])[0]

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            preview = DataLoaderService.get_preview(
                cols, rows, page=page, page_size=page_size,
                search=search, sort_by=sort_by, sort_order=sort_order
            )
            preview["id"] = ds["id"]
            preview["filename"] = ds["filename"]
            self._send_json(preview)
            return

        # Analysis Overview /api/analysis/{id}/overview
        if "/api/analysis/" in path and path.endswith("/overview"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            conn.close()
            if not ds or not os.path.exists(ds["file_path"]):
                self._send_error("Dataset not found", 404)
                return

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            meta = json.loads(ds["metadata_json"] or "{}")
            filter_params = {
                "start_date": params.get("start_date", [None])[0],
                "end_date": params.get("end_date", [None])[0],
                "categories": params.get("category"),
                "regions": params.get("region"),
                "products": params.get("product")
            }
            overview = AnalyticsEngineService.calculate_overview(
                cols, rows, custom_mappings=meta.get("mappings"), filter_params=filter_params
            )
            overview["dataset_id"] = ds["id"]
            overview["filename"] = ds["filename"]
            self._send_json(overview)
            return

        # Analysis Statistics /api/analysis/{id}/statistics
        if "/api/analysis/" in path and path.endswith("/statistics"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            conn.close()
            if not ds or not os.path.exists(ds["file_path"]):
                self._send_error("Dataset not found", 404)
                return

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            eda = EDAEngineService.calculate_eda(cols, rows)
            self._send_json({
                "dataset_id": ds["id"],
                "numerical_stats": eda["numerical_stats"],
                "categorical_stats": eda["categorical_stats"],
                "auto_eda_narrative": eda["auto_summary"]
            })
            return

        # Analysis Correlations /api/analysis/{id}/correlations
        if "/api/analysis/" in path and path.endswith("/correlations"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            conn.close()
            if not ds or not os.path.exists(ds["file_path"]):
                self._send_error("Dataset not found", 404)
                return

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            eda = EDAEngineService.calculate_eda(cols, rows)
            self._send_json(eda["correlation_matrix"])
            return

        # Analysis Charts /api/analysis/{id}/charts
        if "/api/analysis/" in path and path.endswith("/charts"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            conn.close()
            if not ds or not os.path.exists(ds["file_path"]):
                self._send_error("Dataset not found", 404)
                return

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            meta = json.loads(ds["metadata_json"] or "{}")
            filter_params = {
                "start_date": params.get("start_date", [None])[0],
                "end_date": params.get("end_date", [None])[0],
                "categories": params.get("category"),
                "regions": params.get("region"),
                "products": params.get("product")
            }
            charts = AnalyticsEngineService.generate_charts(
                cols, rows, custom_mappings=meta.get("mappings"), filter_params=filter_params
            )
            self._send_json(charts)
            return

        # AI Suggestions /api/ai/suggestions/{dataset_id}
        if path.startswith("/api/ai/suggestions/"):
            dataset_id = int(path.split("/")[4])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            conn.close()
            if not ds:
                self._send_error("Dataset not found", 404)
                return
            cols, _ = DataLoaderService.load_records(ds["file_path"])
            suggs = AIAnalystService.get_suggested_questions(cols)
            self._send_json({"dataset_id": dataset_id, "suggestions": suggs})
            return

        # AI History /api/ai/history/{conversation_id}
        if path.startswith("/api/ai/history/"):
            conversation_id = int(path.split("/")[4])
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,))
            c_row = cursor.fetchone()
            if not c_row:
                conn.close()
                self._send_error("Conversation not found", 404)
                return

            cursor.execute("SELECT id, role, content, query_plan_json, chart_recommendation_json, metrics_context_json, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC", (conversation_id,))
            m_rows = cursor.fetchall()
            conn.close()
            msgs = []
            for m in m_rows:
                msgs.append({
                    "id": m[0],
                    "role": m[1],
                    "content": m[2],
                    "query_plan": json.loads(m[3]) if m[3] else None,
                    "chart_recommendation": json.loads(m[4]) if m[4] else None,
                    "verified_metrics": json.loads(m[5]) if m[5] else None,
                    "created_at": str(m[6])
                })
            self._send_json({"conversation_id": conversation_id, "title": c_row[0], "messages": msgs})
            return

        # Reports List /api/reports
        if path == "/api/reports":
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, dataset_id, report_type, title, file_path, file_format, summary_text, created_at FROM reports ORDER BY id DESC")
            rows = cursor.fetchall()
            conn.close()
            results = []
            for r in rows:
                results.append({
                    "id": r[0],
                    "dataset_id": r[1],
                    "report_type": r[2],
                    "title": r[3],
                    "file_format": r[5],
                    "summary_text": r[6],
                    "download_url": f"/api/reports/{r[0]}/download",
                    "created_at": str(r[7])
                })
            self._send_json(results)
            return

        # Report Download /api/reports/{id}/download
        if path.startswith("/api/reports/") and path.endswith("/download"):
            report_id = int(path.split("/")[3])
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT file_path, file_format FROM reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            conn.close()
            if not row or not os.path.exists(row[0]):
                self._send_error("Report file not found", 404)
                return

            file_path = row[0]
            ext = row[1]
            content_type = "application/pdf" if ext == "pdf" else "text/csv" if ext == "csv" else "text/html"

            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(file_path)}"')
            self.send_header("Content-Length", str(len(content)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
            return

        # Static Frontend file delivery
        frontend_dir = settings.BASE_DIR / "frontend" / "dist"
        if not frontend_dir.exists():
            frontend_dir = settings.BASE_DIR / "frontend" / "public"

        req_file = path.lstrip("/") or "index.html"
        target_path = frontend_dir / req_file

        if not target_path.exists() or target_path.is_dir():
            target_path = frontend_dir / "index.html"

        if target_path.exists() and target_path.is_file():
            mime, _ = mimetypes.guess_type(str(target_path))
            with open(target_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime or "text/html")
            self.send_header("Content-Length", str(len(content)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
            return

        self._send_error("Endpoint not found", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))

        # File Upload /api/datasets/upload (Multipart form data)
        if path == "/api/datasets/upload":
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self._send_error("Expected multipart/form-data", 400)
                return

            boundary = content_type.split("boundary=")[-1].strip()
            raw_body = self.rfile.read(content_length)

            # Parse multipart boundary
            parts = raw_body.split(f"--{boundary}".encode())
            file_data = None
            filename = "uploaded_dataset.csv"

            for p in parts:
                if b'filename="' in p:
                    head, body = p.split(b"\r\n\r\n", 1)
                    body = body.rstrip(b"\r\n--")
                    m = re_fn = None
                    for line in head.decode(errors="ignore").splitlines():
                        if "filename=" in line:
                            filename = line.split('filename="')[-1].split('"')[0]
                            file_data = body
                            break

            if not file_data:
                self._send_error("No file provided in form upload", 400)
                return

            ext = Path(filename).suffix.lower()
            if ext not in settings.ALLOWED_EXTENSIONS:
                self._send_error(f"Unsupported format. Please upload {', '.join(settings.ALLOWED_EXTENSIONS)}", 400)
                return

            dest_path = settings.STORAGE_DATASETS_DIR / f"{Path(filename).stem}_{int(os.times().elapsed * 1000)}{ext}"
            with open(dest_path, "wb") as f:
                f.write(file_data)

            cols, rows = DataLoaderService.load_records(str(dest_path))
            mappings = DataLoaderService.map_columns(cols)
            meta = json.dumps({"columns": cols, "mappings": mappings})

            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE datasets SET is_active = 0")
            cursor.execute("""
                INSERT INTO datasets (filename, file_path, row_count, column_count, file_size_bytes, is_active, is_cleaned, metadata_json)
                VALUES (?, ?, ?, ?, ?, 1, 0, ?)
            """, (filename, str(dest_path), len(rows), len(cols), len(file_data), meta))
            new_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self._send_json({
                "id": new_id,
                "filename": filename,
                "row_count": len(rows),
                "column_count": len(cols),
                "file_size_bytes": len(file_data),
                "is_active": True,
                "is_cleaned": False,
                "parent_id": None,
                "column_names": cols,
                "detected_mappings": mappings,
                "uploaded_at": str(os.path.getctime(dest_path))
            }, 201)
            return

        # Standard JSON body parser
        body = self.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8")) if body else {}

        # Set Active Dataset /api/datasets/{id}/select
        if path.startswith("/api/datasets/") and path.endswith("/select"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE datasets SET is_active = 0")
            cursor.execute("UPDATE datasets SET is_active = 1 WHERE id = ?", (dataset_id,))
            conn.commit()
            conn.close()
            self._send_json({"status": "success", "active_dataset_id": dataset_id})
            return

        # Cleaning Preview /api/cleaning/{id}/preview
        if path.startswith("/api/cleaning/") and path.endswith("/preview"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            conn.close()
            if not ds:
                self._send_error("Dataset not found", 404)
                return

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            insp = DataCleanerService.inspect_dataset(cols, rows)
            insp["dataset_id"] = ds["id"]
            insp["filename"] = ds["filename"]
            self._send_json(insp)
            return

        # Cleaning Apply /api/cleaning/{id}/apply
        if path.startswith("/api/cleaning/") and path.endswith("/apply"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            if not ds:
                conn.close()
                self._send_error("Dataset not found", 404)
                return

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            cleaned_rows, summary = DataCleanerService.apply_cleaning(
                columns=cols,
                rows=rows,
                remove_duplicates=payload.get("remove_duplicates", True),
                fill_numerical=payload.get("fill_numerical", "mean"),
                fill_categorical=payload.get("fill_categorical", "mode"),
                drop_missing_rows=payload.get("drop_missing_rows", False),
                normalize_columns=payload.get("normalize_columns", [])
            )

            final_cols = list(cleaned_rows[0].keys()) if cleaned_rows else cols
            orig_stem = Path(ds["filename"]).stem
            clean_filename = f"{orig_stem}_cleaned.csv"
            dest_path = settings.STORAGE_DATASETS_DIR / f"{orig_stem}_cleaned_{int(os.times().elapsed * 1000)}.csv"

            import csv
            with open(dest_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=final_cols)
                writer.writeheader()
                writer.writerows(cleaned_rows)

            new_mappings = DataLoaderService.map_columns(final_cols)
            meta = json.dumps({"columns": final_cols, "mappings": new_mappings})

            cursor = conn.cursor()
            cursor.execute("UPDATE datasets SET is_active = 0")
            cursor.execute("""
                INSERT INTO datasets (filename, file_path, row_count, column_count, file_size_bytes, is_active, is_cleaned, parent_id, metadata_json)
                VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)
            """, (clean_filename, str(dest_path), len(cleaned_rows), len(final_cols), dest_path.stat().st_size, ds["id"], meta))
            new_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self._send_json({
                "original_dataset_id": ds["id"],
                "cleaned_dataset_id": new_id,
                "filename": clean_filename,
                "rows_before": summary["rows_before"],
                "rows_after": summary["rows_after"],
                "duplicates_removed": summary["duplicates_removed"],
                "missing_imputed_count": summary["missing_imputed_count"],
                "summary_notes": summary["summary_notes"]
            })
            return

        # AI Chat /api/ai/chat
        if path == "/api/ai/chat":
            dataset_id = payload.get("dataset_id")
            message = payload.get("message", "")
            conv_id = payload.get("conversation_id")

            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            if not ds:
                conn.close()
                self._send_error("Active dataset not found", 404)
                return

            cursor = conn.cursor()
            if not conv_id:
                cursor.execute("INSERT INTO conversations (dataset_id, title) VALUES (?, ?)", (ds["id"], f"Chat: {message[:30]}..."))
                conv_id = cursor.lastrowid
                conn.commit()

            cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, 'user', ?)", (conv_id, message))
            conn.commit()

            # Retrieve history
            cursor.execute("SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id ASC", (conv_id,))
            hist_rows = cursor.fetchall()
            history = [{"role": r[0], "content": r[1]} for r in hist_rows]

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            ai_resp = AIAnalystService.generate_response(message, cols, rows, history)

            q_plan_str = json.dumps(ai_resp["query_plan"])
            chart_rec_str = json.dumps(ai_resp["chart_recommendation"]) if ai_resp["chart_recommendation"] else None
            metrics_str = json.dumps(ai_resp["verified_metrics"])

            cursor.execute("""
                INSERT INTO messages (conversation_id, role, content, query_plan_json, chart_recommendation_json, metrics_context_json)
                VALUES (?, 'assistant', ?, ?, ?, ?)
            """, (conv_id, ai_resp["answer"], q_plan_str, chart_rec_str, metrics_str))
            msg_id = cursor.lastrowid
            conn.commit()
            conn.close()

            ai_resp["conversation_id"] = conv_id
            ai_resp["message_id"] = msg_id
            self._send_json(ai_resp)
            return

        # Anomaly Detection /api/anomaly/{id}/detect
        if path.startswith("/api/anomaly/") and path.endswith("/detect"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            conn.close()
            if not ds:
                self._send_error("Dataset not found", 404)
                return

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            res = AnomalyDetectorService.detect_anomalies(
                cols, rows,
                method=payload.get("method", "isolation_forest"),
                metric_column=payload.get("metric_column"),
                contamination_pct=payload.get("contamination_pct", 0.05)
            )
            res["dataset_id"] = ds["id"]
            self._send_json(res)
            return

        # Forecasting /api/forecast/{id}
        if path.startswith("/api/forecast/"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            conn.close()
            if not ds:
                self._send_error("Dataset not found", 404)
                return

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            try:
                fc = ForecastingService.generate_forecast(
                    cols, rows,
                    metric_column=payload.get("metric_column"),
                    date_column=payload.get("date_column"),
                    horizon_days=payload.get("horizon_days", 30),
                    method=payload.get("method", "linear")
                )
                fc["dataset_id"] = ds["id"]
                self._send_json(fc)
            except Exception as e:
                self._send_error(str(e), 400)
            return

        # Report Generation /api/reports/generate
        if path == "/api/reports/generate":
            dataset_id = payload.get("dataset_id")
            report_type = payload.get("report_type", "executive_summary")
            report_format = payload.get("format", "pdf")
            custom_title = payload.get("title")

            conn = self._get_db()
            ds = self._get_active_dataset(conn, dataset_id)
            if not ds:
                conn.close()
                self._send_error("Dataset not found", 404)
                return

            cols, rows = DataLoaderService.load_records(ds["file_path"])
            content = ReportGeneratorService.generate_report_content(
                cols, rows, ds["filename"], report_type, custom_title
            )
            file_path = ReportGeneratorService.export_report_file(content, report_format)

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reports (dataset_id, report_type, title, file_path, file_format, summary_text)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ds["id"], report_type, content["title"], file_path, report_format, content["executive_summary"]))
            rep_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self._send_json({
                "id": rep_id,
                "dataset_id": ds["id"],
                "title": content["title"],
                "report_type": report_type,
                "file_format": report_format,
                "download_url": f"/api/reports/{rep_id}/download",
                "summary_text": content["executive_summary"],
                "created_at": str(os.path.getctime(file_path))
            })
            return

        self._send_error("Not found", 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/datasets/"):
            dataset_id = int(path.split("/")[3])
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM datasets WHERE id = ?", (dataset_id,))
            row = cursor.fetchone()
            if row and os.path.exists(row[0]):
                try:
                    os.remove(row[0])
                except OSError:
                    pass
            cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
            cursor.execute("DELETE FROM conversations WHERE dataset_id = ?", (dataset_id,))
            cursor.execute("DELETE FROM reports WHERE dataset_id = ?", (dataset_id,))
            conn.commit()
            conn.close()
            self._send_json({"status": "success", "deleted_id": dataset_id})
            return
        self._send_error("Not found", 404)

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, InsightIQRequestHandler)
    print(f"\n==================================================")
    print(f"  InsightIQ Backend API Server running on port {port}")
    print(f"  Access URL: http://localhost:{port}")
    print(f"==================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
