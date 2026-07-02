"""
generate_data.py
-----------------
Generates a synthetic e-commerce product catalog modeled on real CPG brands
(Coca-Cola, Nestle, Colgate-Palmolive, Mondelez, Kellogg's) across a retailer
digital shelf.

Why synthetic data instead of scraping Amazon:
  - Amazon's ToS prohibits scraping product data at scale.
  - Real CommerceIQ pipelines ingest data via authorized retailer APIs / feeds,
    not scraping. Synthetic data mirrors that data shape without the legal risk.
  - It also lets us control the exact mix of defects, so we can validate the
    scoring engine against known ground truth (useful for a portfolio project).

Output: data/products.csv
"""

import csv
import random

random.seed(42)

BRANDS = {
    "Coca-Cola": ["Beverages"],
    "Nestle": ["Beverages", "Confectionery", "Breakfast"],
    "Colgate-Palmolive": ["Personal Care", "Home Care"],
    "Mondelez": ["Snacks", "Confectionery"],
    "Kelloggs": ["Breakfast", "Snacks"],
}

CATEGORY_PRODUCTS = {
    "Beverages": ["Cola 12pk Cans", "Diet Cola 2L Bottle", "Sparkling Water 8pk",
                  "Iced Coffee 4pk", "Juice Drink 6pk", "Energy Drink 12pk"],
    "Confectionery": ["Chocolate Bar", "Wafer Bar Multipack", "Candy Bites Bag",
                      "Chocolate Chip Cookies", "Mint Tin"],
    "Breakfast": ["Corn Flakes Cereal", "Granola Bars 6pk", "Instant Oatmeal 8pk",
                  "Toaster Pastries 8pk"],
    "Snacks": ["Cracker Sandwiches", "Cheese Crackers Box", "Pretzel Bag",
               "Trail Mix Pouch", "Chips Family Size"],
    "Personal Care": ["Toothpaste 6oz", "Mouthwash 1L", "Bar Soap 3pk",
                      "Body Wash 18oz"],
    "Home Care": ["Dish Soap 25oz", "All-Purpose Cleaner Spray", "Laundry Detergent 50oz"],
}

RETAILERS = ["Amazon", "Walmart.com", "Target.com", "Instacart", "Kroger.com"]

GOOD_BULLET_POOL = [
    "Made with real ingredients for a taste you'll love",
    "Convenient multipack, perfect for on-the-go or family sharing",
    "No artificial preservatives added",
    "Trusted brand quality, consistent taste every time",
    "Resealable packaging keeps product fresh longer",
]

def rand_title(brand, product):
    variants = [
        f"{brand} {product}",
        f"{brand} - {product}",
        f"{product} by {brand}",
        f"{brand} {product} (Pack of {random.choice([1,4,6,8,12])})",
    ]
    # 15% chance of a genuinely bad/truncated title (real-world defect)
    if random.random() < 0.15:
        return f"{brand} {product.split()[0]}"
    return random.choice(variants)

def rand_bullets():
    n_bullets = random.choices([0, 1, 2, 3, 5], weights=[8, 12, 15, 20, 45])[0]
    return GOOD_BULLET_POOL[:n_bullets]

def rand_bool(p_true):
    return random.random() < p_true

def generate_row(pid):
    brand = random.choice(list(BRANDS.keys()))
    category = random.choice(BRANDS[brand])
    product = random.choice(CATEGORY_PRODUCTS[category])
    retailer = random.choice(RETAILERS)
    title = rand_title(brand, product)
    bullets = rand_bullets()

    has_main_image = rand_bool(0.90)
    has_lifestyle_images = rand_bool(0.55)
    has_a_plus_content = rand_bool(0.35)   # A+ / enhanced brand content — often missing
    in_stock = rand_bool(0.88)
    price_present = rand_bool(0.95)
    star_rating = round(random.uniform(2.8, 4.9), 1) if rand_bool(0.85) else None
    review_count = random.randint(0, 4000) if star_rating else 0

    return {
        "product_id": f"P{pid:05d}",
        "brand": brand,
        "category": category,
        "retailer": retailer,
        "title": title,
        "title_length": len(title),
        "bullet_count": len(bullets),
        "bullets": " | ".join(bullets),
        "has_main_image": has_main_image,
        "has_lifestyle_images": has_lifestyle_images,
        "has_a_plus_content": has_a_plus_content,
        "in_stock": in_stock,
        "price_present": price_present,
        "star_rating": star_rating if star_rating else "",
        "review_count": review_count,
    }

def main(n=200):
    rows = [generate_row(i) for i in range(1, n + 1)]
    fieldnames = list(rows[0].keys())
    with open("data/products.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {n} listings -> data/products.csv")

if __name__ == "__main__":
    main(200)
