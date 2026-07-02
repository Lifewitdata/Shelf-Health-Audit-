# digital-shelf-audit

**93 of 200 product listings failed a content-completeness audit before this tool touched them. Here's what it did about it.**

A rule-based scoring engine that finds incomplete, low-quality e-commerce product listings and auto-drafts fixes — the detection + remediation loop that sits behind "digital shelf optimization" platforms serving CPG brands like Coca-Cola, Nestlé, Colgate-Palmolive, and Kellogg's.

```
catalog (CSV) ──▶ audit_engine.py ──▶ scored + flagged listings
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                                           ▼
              genai_remediation.py                         report_generator.py
              (auto-drafts fixes for                       (brand / category /
               flagged listings)                            retailer rollups)
                        │                                           │
                        └─────────────────┬─────────────────────────┘
                                           ▼
                                dashboard/index.html
```

## See it work

A real listing from the sample catalog, before and after:

| | Before | After |
|---|---|---|
| **Title** | `Nestle Granola Bars 6pk (Pack of 8)` | `Nestle Granola Bars 6pk - Breakfast Essential, Multipack` |
| **Bullets** | *(none — 0 of 5)* | Premium breakfast from Nestle, a trusted household name · Multipack format designed for everyday convenience · Consistent quality pack after pack |
| **Score** | **48.8 — Critical** | flagged, drafted, ready for human review |
| **Why it failed** | Missing lifestyle images, missing A+ content, zero bullets, title too short | — |

This isn't cherry-picked copywriting — it's the literal output of `genai_remediation.py --mode template` running against `data/products.csv`, reproducible by anyone who clones this repo.

## The numbers

Run against a 200-SKU sample catalog spanning 5 brands, 6 categories, 5 retailers:

| Metric | Value |
|---|---|
| Average shelf health score | **72.2 / 100** |
| Healthy (90+) | 24 listings (12%) |
| At Risk / Critical | 93 listings (46.5%) |
| Weakest retailer | Instacart — 69.2 avg |
| Weakest brand | Nestlé — 70.5 avg |
| Remediation drafts generated | 93 / 93 flagged listings |

Full brand/category/retailer breakdowns are in `outputs/summary_by_*.csv` — they're what turned "some listings are bad" into "Instacart specifically is the problem," which is the difference between a data dump and something an ops team can act on.

## Why this exists

CPG brands lose sales when their listings are incomplete on retailer sites, and at the scale these brands operate — thousands of SKUs, five-plus retailers each — nobody's catching that by hand. This project builds the smallest real version of that detection loop: **audit → score → flag with a reason → auto-draft a fix → hand to a human for the final call.**

## How the scoring actually works

Explainability was chosen over sophistication on purpose — an ops analyst reviewing a flagged SKU needs to know *exactly* which rule failed, not an opaque model score.

```python
RULES = [
    rule_bool("has_main_image", 20, "Missing main image"),
    rule_bool("has_a_plus_content", 20, "Missing A+ content"),
    # bullets and title get partial credit, not just pass/fail
    {"weight": 20, "score_fn": lambda r: 20 if r["bullet_count"] >= 3
        else round((r["bullet_count"] / 3) * 20, 1), ...},
    ...
]
assert sum(r["weight"] for r in RULES) == 100
```

Every rule is defined once — weight, scoring function, and failure explanation together — so the score and the reason it's shown to a reviewer can never drift out of sync. An earlier version computed these separately with duplicated thresholds; the refactor was verified with a row-level diff against the old output (**0 of 200 scores changed**) before being merged in.

## Design decisions

- **Synthetic data, deliberately.** Scraping Amazon/Walmart at scale violates their ToS — real platforms ingest via authorized retailer feeds. `data/generate_data.py` mirrors real defect rates (≈10% missing images, ≈65% missing A+ content, ≈15% thin titles) instead of taking a legal shortcut to get "real-looking" data.
- **The GenAI layer is swappable, not hardcoded.** `genai_remediation.py` runs in `--mode template` by default (deterministic, no API key, reproducible for anyone who clones this) or `--mode llm` if `ANTHROPIC_API_KEY` is set, which calls the real Claude API. A demo that silently breaks without a key is worse than one that's honest about its fallback.
- **One bad row never kills the batch.** Remediation failures log and fall back rather than halting the other 92 listings behind one bad SKU.

## Project structure

```
digital-shelf-audit/
├── data/generate_data.py       synthetic catalog generator
├── src/
│   ├── audit_engine.py         scoring engine (rules defined once, see above)
│   ├── genai_remediation.py    content remediation, template + live LLM modes
│   └── report_generator.py     brand / category / retailer rollups
├── dashboard/index.html        self-contained visualization, no server needed
└── outputs/                    generated CSVs from each pipeline stage
```

## Run it

```bash
pip install pandas
python data/generate_data.py && python src/audit_engine.py \
  && python src/genai_remediation.py && python src/report_generator.py
open dashboard/index.html
```

With a real LLM instead of the template fallback:
```bash
export ANTHROPIC_API_KEY=your_key
python src/genai_remediation.py --mode llm
```

## What I'd build next

- Confidence-weighted flagging — a listing missing one field shouldn't rank the same as one missing five
- A feedback loop where accepted/rejected drafts change which fixes get auto-applied vs. escalated to a human
- Historical tracking to catch *regressions* — a listing that was healthy last week and dropped — not just point-in-time snapshots
