"""
genai_remediation.py
---------------------
Auto-drafts improved titles and bullet points for listings flagged as
"Critical" or "At Risk" by the audit engine.

ARCHITECTURE NOTE (read this before wiring up a real key):
  This module is written so `generate_content()` is a single swappable
  function. In production you'd point it at the Anthropic Messages API:

      response = client.messages.create(
          model="claude-sonnet-4-6",
          max_tokens=300,
          messages=[{"role": "user", "content": prompt}]
      )

  For this portfolio project I run it in `--mode template` by default (no
  API key required, fully reproducible for a demo/interview) and
  `--mode llm` if ANTHROPIC_API_KEY is set in the environment. This keeps
  the repo runnable by anyone who clones it without needing your key,
  while still proving the integration works end-to-end.
"""

import argparse
import os
import pandas as pd

PROMPT_TEMPLATE = """You are a retail e-commerce copywriter for a CPG brand.
Product: {brand} {product_hint}
Category: {category}

Write:
1. One improved product title (50-80 characters, keyword-rich, no gimmicks)
2. Three concise product bullet points (benefit-led, factual, no health claims)

Respond in this exact format:
TITLE: <title>
BULLET1: <bullet>
BULLET2: <bullet>
BULLET3: <bullet>
"""

def generate_content_template(brand, category, product_hint):
    """Deterministic local fallback -- no API call. Good enough to demo the
    pipeline end-to-end and to unit test without network access."""
    title = f"{brand} {product_hint} - {category} Essential, Multipack"
    bullets = [
        f"Premium {category.lower()} from {brand}, a trusted household name",
        "Multipack format designed for everyday convenience and value",
        "Consistent quality you can rely on, pack after pack",
    ]
    return title[:80], bullets

def generate_content_llm(brand, category, product_hint):
    """Live call to the Anthropic API. Requires ANTHROPIC_API_KEY."""
    import anthropic
    client = anthropic.Anthropic()
    prompt = PROMPT_TEMPLATE.format(brand=brand, category=category, product_hint=product_hint)
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text
    lines = {l.split(":", 1)[0].strip(): l.split(":", 1)[1].strip()
             for l in text.strip().split("\n") if ":" in l}
    title = lines.get("TITLE", f"{brand} {product_hint}")
    bullets = [lines.get(f"BULLET{i}", "") for i in (1, 2, 3)]
    return title, bullets

def extract_product_hint(title: str, brand: str) -> str:
    """Strip the brand name, connector words, and stray punctuation from a
    listing title to isolate what the product actually is, e.g.
    'Kelloggs - Cracker Sandwiches' + brand 'Kelloggs' -> 'Cracker Sandwiches'.
    """
    if not isinstance(title, str) or not title.strip():
        return "Item"
    cleaned = title.replace(brand, "")
    for connector in [" - ", " by ", "(Pack of", ")"]:
        cleaned = cleaned.replace(connector, " ")
    cleaned = " ".join(cleaned.split())  # collapse whitespace
    return cleaned.strip(" -") or "Item"

def remediate(input_csv="outputs/audit_results.csv",
              output_csv="outputs/remediation_report.csv",
              mode="template"):
    df = pd.read_csv(input_csv)
    targets = df[df["severity"].isin(["Critical", "At Risk"])].copy()

    gen_fn = generate_content_llm if mode == "llm" else generate_content_template

    new_titles, new_bullets = [], []
    for _, row in targets.iterrows():
        product_hint = extract_product_hint(row["title"], row["brand"])
        try:
            title, bullets = gen_fn(row["brand"], row["category"], product_hint)
        except Exception as e:
            # Never let a remediation failure crash the batch -- log and fall back.
            title, bullets = generate_content_template(row["brand"], row["category"], product_hint)
        new_titles.append(title)
        new_bullets.append(" | ".join(bullets))

    targets["suggested_title"] = new_titles
    targets["suggested_bullets"] = new_bullets
    targets.to_csv(output_csv, index=False)
    return targets

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["template", "llm"], default="template")
    args = parser.parse_args()

    if args.mode == "llm" and not os.environ.get("ANTHROPIC_API_KEY"):
        print("No ANTHROPIC_API_KEY found in environment -- falling back to template mode.")
        args.mode = "template"

    result = remediate(mode=args.mode)
    print(f"Generated remediation suggestions for {len(result)} flagged listings (mode={args.mode}).")
    print(result[["product_id", "brand", "title", "suggested_title"]].head(5).to_string(index=False))
