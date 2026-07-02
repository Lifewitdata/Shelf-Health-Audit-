"""
report_generator.py
--------------------
Rolls up listing-level audit results into brand and category summaries --
the level a CPG account manager or ops lead actually consumes, rather than
raw per-SKU data.
"""

import pandas as pd

def generate_summary(input_csv="outputs/audit_results.csv"):
    df = pd.read_csv(input_csv)

    brand_summary = df.groupby("brand").agg(
        avg_score=("shelf_health_score", "mean"),
        listings=("product_id", "count"),
        critical_count=("severity", lambda s: (s == "Critical").sum()),
        at_risk_count=("severity", lambda s: (s == "At Risk").sum()),
    ).round(1).sort_values("avg_score")

    category_summary = df.groupby("category").agg(
        avg_score=("shelf_health_score", "mean"),
        listings=("product_id", "count"),
    ).round(1).sort_values("avg_score")

    retailer_summary = df.groupby("retailer").agg(
        avg_score=("shelf_health_score", "mean"),
        listings=("product_id", "count"),
    ).round(1).sort_values("avg_score")

    brand_summary.to_csv("outputs/summary_by_brand.csv")
    category_summary.to_csv("outputs/summary_by_category.csv")
    retailer_summary.to_csv("outputs/summary_by_retailer.csv")

    return brand_summary, category_summary, retailer_summary

if __name__ == "__main__":
    b, c, r = generate_summary()
    print("=== Shelf Health by Brand ===")
    print(b.to_string())
    print("\n=== Shelf Health by Category ===")
    print(c.to_string())
    print("\n=== Shelf Health by Retailer ===")
    print(r.to_string())
