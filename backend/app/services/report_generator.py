import os
import csv
import json
from datetime import datetime
from typing import Any, Optional
from backend.app.config import settings
from backend.app.services.data_loader import DataLoaderService
from backend.app.services.analytics_engine import AnalyticsEngineService
from backend.app.services.anomaly_detector import AnomalyDetectorService
from backend.app.services.forecasting import ForecastingService

class ReportGeneratorService:
    @staticmethod
    def generate_report_content(
        columns: list[str],
        rows: list[dict[str, Any]],
        dataset_name: str,
        report_type: str = "executive_summary",
        custom_title: Optional[str] = None
    ) -> dict[str, Any]:
        """Calculates all sections and verified statistics for an analytical report."""
        mappings = DataLoaderService.map_columns(columns)
        overview = AnalyticsEngineService.calculate_overview(columns, rows, mappings)
        charts = AnalyticsEngineService.generate_charts(columns, rows, mappings)
        anomalies_res = AnomalyDetectorService.detect_anomalies(columns, rows)

        # Forecast summary if date exists
        forecast_summary = "Chronological forecasting not available due to missing date dimension."
        try:
            if mappings.get("date"):
                fc = ForecastingService.generate_forecast(columns, rows, horizon_days=30)
                forecast_summary = (
                    f"30-day projection indicates a {fc['trend_direction']} trend with estimated "
                    f"forecast accuracy (MAPE) of {fc['accuracy']['mape']}%."
                )
        except Exception:
            pass

        title = custom_title or f"InsightIQ – {report_type.replace('_', ' ').title()} Report"

        # Executive summary narrative
        kpis = overview["kpis"]
        rev_kpi = next((k for k in kpis if k["id"] == "total_revenue"), None)
        profit_kpi = next((k for k in kpis if k["id"] == "total_profit"), None)
        margin_kpi = next((k for k in kpis if k["id"] == "profit_margin"), None)
        orders_kpi = next((k for k in kpis if k["id"] == "total_orders"), None)

        rev_str = rev_kpi["formatted_value"] if rev_kpi else "N/A"
        profit_str = profit_kpi["formatted_value"] if profit_kpi else "N/A"
        margin_str = margin_kpi["formatted_value"] if margin_kpi else "N/A"
        orders_str = orders_kpi["formatted_value"] if orders_kpi else f"{len(rows):,}"

        exec_summary = (
            f"This comprehensive {report_type.replace('_', ' ')} evaluates commercial performance for dataset '{dataset_name}'. "
            f"During the analyzed operating cycle, the business recorded {orders_str} transactions, generating a cumulative "
            f"revenue of {rev_str} and net profit of {profit_str} (net profit margin: {margin_str}). Overall commercial efficiency "
            f"demonstrates sustainable operating dynamics across active business divisions."
        )

        trends = []
        rev_trend = charts.get("revenue_over_time", [])
        if len(rev_trend) >= 2:
            first_p = rev_trend[0]
            last_p = rev_trend[-1]
            diff = last_p["revenue"] - first_p["revenue"]
            pct = (diff / first_p["revenue"] * 100) if first_p["revenue"] > 0 else 0
            trends.append(f"Revenue trajectory shifted from ${first_p['revenue']:,.2f} ({first_p['period']}) to ${last_p['revenue']:,.2f} ({last_p['period']}), representing a {pct:+.1f}% shift.")
        trends.append(f"The top-performing category generated ${charts['profit_by_category'][0]['revenue']:,.2f} in gross revenue." if charts["profit_by_category"] else "Portfolio distribution remains balanced.")

        # Anomalies summary
        anomaly_notes = []
        for an in anomalies_res.get("anomalies", [])[:3]:
            anomaly_notes.append(
                f"Record {an['record_id']} ({an['date'] or 'Date N/A'}): {an['metric']} of ${an['actual_value']:,.2f} ({an['severity']} severity) - {an['reason']}"
            )
        if not anomaly_notes:
            anomaly_notes.append("No critical operational anomalies detected in active records.")

        recommendations = [
            "Double down on marketing spend for top margin product categories.",
            "Establish automated inventory alerts for categories exhibiting strong growth momentum.",
            "Review discount structures for outliers flagged in low-profit transactions to avoid margin erosion.",
            "Standardize client retention workflows to increase repeat customer transaction frequency."
        ]

        return {
            "title": title,
            "report_type": report_type,
            "dataset_name": dataset_name,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "executive_summary": exec_summary,
            "kpis": kpis,
            "trends": trends,
            "category_analysis": charts.get("profit_by_category", [])[:8],
            "regional_analysis": charts.get("sales_by_region", [])[:8],
            "anomalies_summary": anomaly_notes,
            "forecast_summary": forecast_summary,
            "strategic_recommendations": recommendations
        }

    @staticmethod
    def export_report_file(
        report_content: dict[str, Any],
        report_format: str = "pdf",
        output_filename: Optional[str] = None
    ) -> str:
        """Exports the generated report content to PDF, CSV, or Excel file."""
        settings.STORAGE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = output_filename or f"InsightIQ_Report_{timestamp}"

        if report_format == "csv":
            file_path = settings.STORAGE_REPORTS_DIR / f"{base_name}.csv"
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["InsightIQ Business Intelligence Report"])
                writer.writerow(["Title", report_content["title"]])
                writer.writerow(["Dataset", report_content["dataset_name"]])
                writer.writerow(["Generated At", report_content["generated_at"]])
                writer.writerow([])
                writer.writerow(["--- KEY PERFORMANCE INDICATORS ---"])
                writer.writerow(["Metric", "Value", "Formatted"])
                for k in report_content["kpis"]:
                    writer.writerow([k["label"], k["value"], k["formatted_value"]])
                writer.writerow([])
                writer.writerow(["--- CATEGORY ANALYSIS ---"])
                writer.writerow(["Category", "Revenue", "Profit", "Margin %", "Orders"])
                for c in report_content["category_analysis"]:
                    writer.writerow([c["category"], c["revenue"], c["profit"], c.get("margin_pct", 0), c["orders"]])
                writer.writerow([])
                writer.writerow(["--- REGIONAL ANALYSIS ---"])
                writer.writerow(["Region", "Revenue", "Profit", "Orders"])
                for r in report_content["regional_analysis"]:
                    writer.writerow([r["region"], r["revenue"], r["profit"], r["orders"]])
            return str(file_path)

        elif report_format in ("xlsx", "excel"):
            # Check if openpyxl is available, else fallback to formatted CSV
            file_path = settings.STORAGE_REPORTS_DIR / f"{base_name}.xlsx"
            try:
                import openpyxl
                from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Executive Summary"

                # Title styling
                ws["A1"] = report_content["title"]
                ws["A1"].font = Font(size=16, bold=True, color="1E293B")
                ws["A2"] = f"Dataset: {report_content['dataset_name']} | Generated: {report_content['generated_at']}"
                ws["A2"].font = Font(size=10, italic=True, color="64748B")

                # KPIs Table
                ws["A4"] = "KEY PERFORMANCE INDICATORS"
                ws["A4"].font = Font(bold=True, color="0F172A")
                ws.append(["Metric", "Value", "Benchmark"])
                for k in report_content["kpis"]:
                    ws.append([k["label"], k["formatted_value"], k.get("subtext", "")])

                # Categories
                r_idx = ws.max_row + 2
                ws.cell(row=r_idx, column=1, value="CATEGORY BREAKDOWN").font = Font(bold=True)
                ws.append(["Category", "Revenue ($)", "Profit ($)", "Margin (%)", "Transactions"])
                for c in report_content["category_analysis"]:
                    ws.append([c["category"], c["revenue"], c["profit"], c.get("margin_pct", 0), c["orders"]])

                wb.save(file_path)
                return str(file_path)
            except Exception:
                # Fallback to CSV if openpyxl not installed
                return ReportGeneratorService.export_report_file(report_content, "csv", base_name)

        else:
            # PDF Format
            file_path = settings.STORAGE_REPORTS_DIR / f"{base_name}.pdf"
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

                doc = SimpleDocTemplate(str(file_path), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                styles = getSampleStyleSheet()

                title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#0F172A'), spaceAfter=8)
                sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#64748B'), spaceAfter=14)
                h2_style = ParagraphStyle('Heading2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1E293B'), spaceBefore=12, spaceAfter=6)
                body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#334155'), leading=14)

                story = []
                story.append(Paragraph(report_content["title"], title_style))
                story.append(Paragraph(f"Dataset: <b>{report_content['dataset_name']}</b> | Generated: {report_content['generated_at']}", sub_style))
                story.append(Spacer(1, 10))

                story.append(Paragraph("1. Executive Summary", h2_style))
                story.append(Paragraph(report_content["executive_summary"], body_style))
                story.append(Spacer(1, 12))

                # KPI Table
                story.append(Paragraph("2. Key Performance Indicators", h2_style))
                kpi_data = [["Metric", "Value", "Context"]]
                for k in report_content["kpis"]:
                    kpi_data.append([k["label"], k["formatted_value"], k.get("subtext", "")])
                t_kpi = Table(kpi_data, colWidths=[180, 140, 200])
                t_kpi.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ]))
                story.append(t_kpi)
                story.append(Spacer(1, 14))

                # Category Analysis Table
                story.append(Paragraph("3. Category Performance", h2_style))
                cat_data = [["Category", "Revenue", "Profit", "Margin %", "Orders"]]
                for c in report_content["category_analysis"][:6]:
                    cat_data.append([c["category"], f"${c['revenue']:,.2f}", f"${c['profit']:,.2f}", f"{c.get('margin_pct', 0)}%", str(c['orders'])])
                t_cat = Table(cat_data, colWidths=[140, 100, 100, 90, 90])
                t_cat.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ]))
                story.append(t_cat)
                story.append(Spacer(1, 14))

                story.append(Paragraph("4. Strategic Recommendations", h2_style))
                for idx, rec in enumerate(report_content["strategic_recommendations"], 1):
                    story.append(Paragraph(f"<b>{idx}.</b> {rec}", body_style))
                    story.append(Spacer(1, 4))

                doc.build(story)
                return str(file_path)
            except Exception as e:
                # If ReportLab fails or is not installed, output formatted HTML/text report
                html_path = settings.STORAGE_REPORTS_DIR / f"{base_name}.html"
                kpi_rows = "".join(f"<tr><td>{k['label']}</td><td>{k['formatted_value']}</td></tr>" for k in report_content["kpis"])
                rec_rows = "".join(f"<li>{r}</li>" for r in report_content["strategic_recommendations"])
                html_content = (
                    f"<html><head><title>{report_content['title']}</title>"
                    "<style>body{font-family:sans-serif;padding:30px;line-height:1.6;color:#1e293b}"
                    "h1{color:#0f172a}table{border-collapse:collapse;width:100%;margin:15px 0}"
                    "th,td{border:1px solid #cbd5e1;padding:8px;text-align:left}"
                    "th{background:#0f172a;color:white}</style></head><body>"
                    f"<h1>{report_content['title']}</h1>"
                    f"<p><em>Dataset: {report_content['dataset_name']} | Generated: {report_content['generated_at']}</em></p>"
                    f"<h2>Executive Summary</h2><p>{report_content['executive_summary']}</p>"
                    f"<h2>Key Performance Indicators</h2><table><tr><th>Metric</th><th>Value</th></tr>{kpi_rows}</table>"
                    f"<h2>Recommendations</h2><ol>{rec_rows}</ol></body></html>"
                )
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                return str(html_path)
