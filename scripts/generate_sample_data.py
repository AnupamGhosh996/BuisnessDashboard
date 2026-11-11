import os
import csv
import random
from datetime import datetime, timedelta

def generate_sample_data():
    os.makedirs("storage/datasets", exist_ok=True)
    random.seed(42)

    categories_products = {
        "Hardware": [
            ("Quantum Pro Laptop", 1299.00, 0.28),
            ("UltraWide 4K Monitor", 599.00, 0.35),
            ("Executive Workstation", 1899.00, 0.25),
            ("MicroServer Mini", 749.00, 0.30),
        ],
        "Enterprise Software": [
            ("CloudSync SaaS License", 249.00, 0.72),
            ("CyberShield Security Suite", 499.00, 0.68),
            ("InsightAI Analytics Seat", 199.00, 0.75),
            ("DataPipe ETL Tool", 399.00, 0.65),
        ],
        "Peripherals": [
            ("Apex Wireless Mouse", 49.00, 0.45),
            ("MechanoKey Pro Keyboard", 119.00, 0.40),
            ("AcousticNoise Headset", 149.00, 0.42),
            ("4K UltraStream Webcam", 129.00, 0.38),
        ],
        "Office Equipment": [
            ("ErgoComfort Smart Desk", 699.00, 0.32),
            ("LumberSupport Mesh Chair", 349.00, 0.35),
            ("Acoustic Sound Pod", 999.00, 0.28),
            ("OptiPrint Laser Hub", 449.00, 0.30),
        ],
        "Networking": [
            ("GigaSwitch 24-Port", 299.00, 0.36),
            ("MeshWave WiFi 6 Router", 189.00, 0.40),
            ("OptiFiber Transceiver", 89.00, 0.50),
            ("SecureEdge VPN Gateway", 549.00, 0.48),
        ]
    }

    regions = ["North America", "Europe", "Asia-Pacific", "Latin America", "Middle East"]
    customer_ids = [f"CUST-{1000 + i}" for i in range(1, 121)]

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range_days = (end_date - start_date).days

    records = []
    order_id_counter = 10000

    categories = list(categories_products.keys())

    # Generate 800 regular records with seasonal trends
    for _ in range(800):
        order_id_counter += 1
        order_id = f"ORD-{order_id_counter}"

        # Weight dates towards Q3 and Q4 to create realistic growth trend
        random_day = int(random.triangular(0, date_range_days, date_range_days * 0.75))
        order_date = (start_date + timedelta(days=random_day)).strftime("%Y-%m-%d")

        category = random.choices(categories, weights=[30, 25, 20, 15, 10])[0]
        prod_tuple = random.choice(categories_products[category])
        product, base_price, target_margin = prod_tuple

        region = random.choices(regions, weights=[35, 25, 20, 12, 8])[0]
        customer_id = random.choice(customer_ids)

        # Quantity
        if category == "Enterprise Software":
            quantity = random.choices([1, 2, 5, 10, 20], weights=[40, 30, 15, 10, 5])[0]
        elif category == "Hardware":
            quantity = random.choices([1, 2, 3, 5], weights=[60, 25, 10, 5])[0]
        else:
            quantity = random.randint(1, 8)

        # Price variation (+- 5%)
        price_jitter = random.uniform(0.95, 1.05)
        unit_price = round(base_price * price_jitter, 2)

        revenue = round(quantity * unit_price, 2)

        # Cost calculation based on target margin
        actual_margin = target_margin * random.uniform(0.92, 1.08)
        cost = round(revenue * (1.0 - actual_margin), 2)
        profit = round(revenue - cost, 2)

        records.append({
            "Order ID": order_id,
            "Order Date": order_date,
            "Product": product,
            "Category": category,
            "Region": region,
            "Customer ID": customer_id,
            "Quantity": quantity,
            "Unit Price": unit_price,
            "Revenue": revenue,
            "Cost": cost,
            "Profit": profit
        })

    # Sort chronologically by Order Date
    records.sort(key=lambda r: r["Order Date"])

    # Add deliberate statistical anomalies for Module 6 (Anomaly Detection)
    # Anomaly 1: Massive enterprise order in November
    records.append({
        "Order ID": "ORD-ANOMALY-1",
        "Order Date": "2024-11-15",
        "Product": "Executive Workstation",
        "Category": "Hardware",
        "Region": "North America",
        "Customer ID": "CUST-1099",
        "Quantity": 25,
        "Unit Price": 1899.00,
        "Revenue": 47475.00,
        "Cost": 33232.50,
        "Profit": 14242.50
    })

    # Anomaly 2: Extreme loss-leader / negative profit outlier
    records.append({
        "Order ID": "ORD-ANOMALY-2",
        "Order Date": "2024-06-20",
        "Product": "Quantum Pro Laptop",
        "Category": "Hardware",
        "Region": "Europe",
        "Customer ID": "CUST-1042",
        "Quantity": 15,
        "Unit Price": 699.00,  # steep discount
        "Revenue": 10485.00,
        "Cost": 14250.00,      # regular cost
        "Profit": -3765.00     # major negative profit
    })

    # Write clean dataset
    clean_csv_path = "storage/datasets/clean_sales_dataset.csv"
    fieldnames = list(records[0].keys())
    with open(clean_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated clean dataset with {len(records)} rows at: {clean_csv_path}")

    # Now create sample dataset with deliberate data issues for Module 2 (Data Cleaning)
    dirty_records = [dict(r) for r in records]

    # Add 3 duplicate rows
    dirty_records.append(dict(records[10]))
    dirty_records.append(dict(records[50]))
    dirty_records.append(dict(records[120]))

    # Inject 4 missing values
    dirty_records[25]["Quantity"] = ""
    dirty_records[85]["Region"] = ""
    dirty_records[140]["Cost"] = ""
    dirty_records[210]["Category"] = ""

    sample_csv_path = "storage/datasets/sample_sales_dataset.csv"
    with open(sample_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dirty_records)

    print(f"Generated sample dataset with {len(dirty_records)} rows at: {sample_csv_path}")

    # Also compute and display verification statistics
    valid_records = [r for r in records]
    total_revenue = sum(r["Revenue"] for r in valid_records)
    total_profit = sum(r["Profit"] for r in valid_records)
    total_orders = len(valid_records)
    avg_order_value = total_revenue / total_orders if total_orders else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0

    print("\n--- BASELINE METRICS FOR VERIFICATION ---")
    print(f"Total Orders:        {total_orders}")
    print(f"Total Revenue:       ${total_revenue:,.2f}")
    print(f"Total Profit:        ${total_profit:,.2f}")
    print(f"Average Order Value: ${avg_order_value:,.2f}")
    print(f"Profit Margin:       {profit_margin:.2f}%")

if __name__ == "__main__":
    generate_sample_data()
