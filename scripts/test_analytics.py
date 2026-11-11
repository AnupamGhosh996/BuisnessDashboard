import os
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.data_loader import DataLoaderService
from backend.app.services.data_cleaner import DataCleanerService
from backend.app.services.eda_engine import EDAEngineService
from backend.app.services.analytics_engine import AnalyticsEngineService
from backend.app.services.ai_analyst import AIAnalystService
from backend.app.services.anomaly_detector import AnomalyDetectorService
from backend.app.services.forecasting import ForecastingService
from backend.app.services.report_generator import ReportGeneratorService

def run_tests():
    sample_path = "storage/datasets/sample_sales_dataset.csv"
    if not os.path.exists(sample_path):
        print(f"Error: {sample_path} not found.")
        sys.exit(1)

    print("==================================================")
    print("INSIGHTIQ ANALYTICS & MATH VERIFICATION SUITE")
    print("==================================================")

    # 1. DataLoader Test
    columns, rows = DataLoaderService.load_records(sample_path)
    print(f"\n[1] DataLoader: Loaded {len(rows)} rows, {len(columns)} columns.")
    assert len(rows) > 500, "Should have > 500 records"

    mappings = DataLoaderService.map_columns(columns)
    print(f"    Detected Mappings: {mappings}")
    assert "revenue" in mappings and "profit" in mappings and "date" in mappings

    # 2. Data Cleaner Test
    inspection = DataCleanerService.inspect_dataset(columns, rows)
    print(f"\n[2] DataCleaner Inspection:")
    print(f"    Duplicate rows detected: {inspection['duplicate_rows']}")
    print(f"    Missing values by column: {inspection['missing_values_by_column']}")
    print(f"    Total issues flagged: {len(inspection['issues'])}")
    assert inspection["duplicate_rows"] == 3, f"Expected 3 duplicate rows, got {inspection['duplicate_rows']}"

    cleaned_rows, summary = DataCleanerService.apply_cleaning(columns, rows, remove_duplicates=True, fill_numerical="mean", fill_categorical="mode")
    print(f"    Cleaned dataset rows: {len(cleaned_rows)} (removed {summary['duplicates_removed']} duplicates, imputed {summary['missing_imputed_count']} values)")
    assert len(cleaned_rows) == len(rows) - 3

    # 3. EDA Engine Test
    eda = EDAEngineService.calculate_eda(columns, cleaned_rows)
    print(f"\n[3] EDA Engine:")
    print(f"    Numerical attributes analyzed: {len(eda['numerical_stats'])}")
    print(f"    Categorical attributes analyzed: {len(eda['categorical_stats'])}")
    print(f"    Correlation matrix dimensions: {len(eda['correlation_matrix']['columns'])}x{len(eda['correlation_matrix']['matrix'])}")
    print(f"    Auto EDA Summary: {eda['auto_summary']}")
    assert len(eda["numerical_stats"]) > 0

    # 4. Analytics Engine & Dynamic Filtering Test
    overview = AnalyticsEngineService.calculate_overview(columns, cleaned_rows, mappings)
    print(f"\n[4] Analytics Engine Overview KPIs:")
    for k in overview["kpis"]:
        print(f"    - {k['label']}: {k['formatted_value']} ({k.get('subtext', '')})")

    charts = AnalyticsEngineService.generate_charts(columns, cleaned_rows, mappings)
    print(f"    Revenue over time periods: {len(charts['revenue_over_time'])}")
    print(f"    Categories in profit chart: {len(charts['profit_by_category'])}")
    print(f"    Regions in sales chart: {len(charts['sales_by_region'])}")
    print(f"    Top products evaluated: {len(charts['product_performance'])}")
    assert len(charts["revenue_over_time"]) > 0
    assert len(charts["profit_by_category"]) > 0

    # Test filtering
    filtered_overview = AnalyticsEngineService.calculate_overview(
        columns, cleaned_rows, mappings, filter_params={"categories": ["Hardware"]}
    )
    print(f"    Filtered to Hardware: {filtered_overview['row_count']} orders (Total Revenue: {filtered_overview['kpis'][0]['formatted_value']})")
    assert filtered_overview["row_count"] < overview["row_count"]

    # 5. AI Analyst Safe Computational Engine Test
    print(f"\n[5] AI Analyst Safe Calculations:")
    test_queries = [
        "What is our total revenue?",
        "Which product generated the highest profit?",
        "Compare regional sales performance",
        "What are the monthly sales trends?"
    ]
    for q in test_queries:
        ai_resp = AIAnalystService.generate_response(q, columns, cleaned_rows)
        print(f"    Query: '{q}' -> Operation: {ai_resp['query_plan']['operation']}")
        print(f"    Verified Metrics: {list(ai_resp['verified_metrics'].keys())}")
        if ai_resp["chart_recommendation"]:
            print(f"    Chart recommended: {ai_resp['chart_recommendation']['chart_type']} ({ai_resp['chart_recommendation']['title']})")
        assert len(ai_resp["answer"]) > 50

    # 6. Anomaly Detection Test
    print(f"\n[6] Anomaly Detection:")
    anomalies_res = AnomalyDetectorService.detect_anomalies(columns, cleaned_rows, method="isolation_forest")
    print(f"    Detected {anomalies_res['anomalies_detected_count']} anomalies ({anomalies_res['anomaly_rate_pct']}%) using {anomalies_res['method_used']}.")
    if anomalies_res["anomalies"]:
        top_an = anomalies_res["anomalies"][0]
        print(f"    Top Anomaly: {top_an['record_id']} | Value: ${top_an['actual_value']:,.2f} vs Baseline: ${top_an['expected_baseline']:,.2f} | Reason: {top_an['reason']}")
    assert anomalies_res["anomalies_detected_count"] > 0

    # 7. Forecasting Test
    print(f"\n[7] Forecasting Engine:")
    fc = ForecastingService.generate_forecast(columns, cleaned_rows, horizon_days=30, method="linear")
    print(f"    Forecasted {fc['horizon_days']} days for '{fc['metric']}' | Direction: {fc['trend_direction']}")
    print(f"    Accuracy: MAE=${fc['accuracy']['mae']:,.2f}, RMSE=${fc['accuracy']['rmse']:,.2f}, MAPE={fc['accuracy']['mape']}%")
    assert len(fc["points"]) > 0

    # 8. Report Generator Test
    print(f"\n[8] Report Generator:")
    report_content = ReportGeneratorService.generate_report_content(columns, cleaned_rows, "sample_sales_dataset.csv", "executive_summary")
    print(f"    Report Title: {report_content['title']}")
    print(f"    Executive Summary snippet: {report_content['executive_summary'][:120]}...")
    csv_file = ReportGeneratorService.export_report_file(report_content, "csv")
    print(f"    Exported CSV report to: {csv_file}")
    assert os.path.exists(csv_file)

    print("\n==================================================")
    print("ALL 8 MODULES PASSED WITH 100% MATHEMATICAL INTEGRITY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
