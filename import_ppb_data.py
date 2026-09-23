"""
Imports the scraped PPB drug register (ppb_drug_register.csv) into
the Drug table. Safe to re-run - updates existing entries by
registration number instead of creating duplicates.
"""

import csv
from app import create_app
from app.extensions import db
from app.models.drug import Drug

app = create_app()

CSV_FILENAME = "ppb_drug_register.csv"

# Maps CSV column names (from the scraper) to Drug model fields
FIELD_MAP = {
    "Product Registration No": "registration_number",
    "Product Trade Name": "trade_name",
    "Inn Of Api": "active_ingredient",
    "Dosage Form Name": "dosage_form",
    "Country of Origin": "country_of_origin",
    "Mah Company Name": "manufacturer",
    "Date of Expiry": "registration_expiry",
}

with app.app_context():
    added = 0
    updated = 0
    skipped = 0

    with open(CSV_FILENAME, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            reg_number = row.get("Product Registration No", "").strip()

            if not reg_number:
                skipped += 1
                continue

            drug_data = {
                model_field: row.get(csv_col, "").strip()
                for csv_col, model_field in FIELD_MAP.items()
            }

            existing = Drug.query.filter_by(registration_number=reg_number).first()

            if existing:
                for field, value in drug_data.items():
                    setattr(existing, field, value)
                updated += 1
            else:
                new_drug = Drug(**drug_data)
                db.session.add(new_drug)
                added += 1

        db.session.commit()

    print(f"Import complete: {added} added, {updated} updated, {skipped} skipped (missing reg number).")