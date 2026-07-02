"""
audit_engine.py

Scores product listings 0-100 on content completeness. Each rule is defined
ONCE (a check function + weight + human-readable issue text) and both the
score and the issue list are derived from that single definition -- so a
rule can never go out of sync with its own explanation.
"""

import pandas as pd


def rule_bool(field, weight, issue_text):
    """Factory for simple present/absent rules."""
    return {
        "weight": weight,
        "score_fn": lambda row: weight if row[field] else 0,
        "failed": lambda row: not row[field],
        "issue": issue_text,
    }


RULES = [
    rule_bool("has_main_image", 20, "Missing main image"),
    rule_bool("has_lifestyle_images", 10, "Missing lifestyle images"),
    rule_bool("has_a_plus_content", 20, "Missing A+ content"),
    rule_bool("in_stock", 10, "Out of stock"),
    rule_bool("price_present", 10, "Price missing"),
    {
        "weight": 20,
        "score_fn": lambda row: 20 if row["bullet_count"] >= 3
            else round((row["bullet_count"] / 3) * 20, 1),
        "failed": lambda row: row["bullet_count"] < 3,
        "issue": lambda row: f"Thin bullets ({row['bullet_count']}/5)",
    },
    {
        "weight": 10,
        "score_fn": lambda row: 10 if row["title_length"] >= 40
            else round((row["title_length"] / 40) * 10, 1),
        "failed": lambda row: row["title_length"] < 40,
        "issue": "Title too short",
    },
]

assert sum(r["weight"] for r in RULES) == 100, "Rule weights must sum to 100"


def score_row(row):
    total = sum(rule["score_fn"](row) for rule in RULES)
    issues = []
    for rule in RULES:
        if rule["failed"](row):
            text = rule["issue"](row) if callable(rule["issue"]) else rule["issue"]
            issues.append(text)
    return round(total, 1), "; ".join(issues) if issues else "None"


def severity_band(score: float) -> str:
    if score >= 90:
        return "Healthy"
    elif score >= 70:
        return "Needs Minor Fixes"
    elif score >= 50:
        return "At Risk"
    return "Critical"


def run_audit(input_csv="data/products.csv", output_csv="outputs/audit_results.csv"):
    df = pd.read_csv(input_csv)

    results = df.apply(score_row, axis=1)
    df["shelf_health_score"] = results.apply(lambda x: x[0])
    df["issues"] = results.apply(lambda x: x[1])
    df["severity"] = df["shelf_health_score"].apply(severity_band)

    df.to_csv(output_csv, index=False)
    return df


if __name__ == "__main__":
    df = run_audit()
    print(f"Audited {len(df)} listings.")
    print(df["severity"].value_counts())
    print(f"\nAvg shelf health score: {df['shelf_health_score'].mean():.1f}")
