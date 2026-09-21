"""
Seeds the database with a handful of sample drugs for local testing.
Replace this with real PPB data once the scraper is finished.
"""

from app import create_app
from app.extensions import db
from app.models.drug import Drug

app = create_app()

sample_drugs = [
    {
        "registration_number": "H2009/19973/558/R1",
        "trade_name": "LYSOFLAM TABLETS",
        "active_ingredient": "Paracetamol/Diclofenac/Serratiopeptidase",
        "dosage_form": "Tablet",
        "country_of_origin": "India",
        "manufacturer": "Cachet Pharmaceuticals",
        "registration_expiry": "2027-03-15",
    },
    {
        "registration_number": "H2009/19964/197/R1",
        "trade_name": "Clavulin Suspension 457mg/5ml",
        "active_ingredient": "Amoxicillin + Clavulanate",
        "dosage_form": "Powder For Suspension",
        "country_of_origin": "UK",
        "manufacturer": "GlaxoSmithKline",
        "registration_expiry": "2026-11-20",
    },
    {
        "registration_number": "H2015/00123/001",
        "trade_name": "Panadol Extra",
        "active_ingredient": "Paracetamol/Caffeine",
        "dosage_form": "Tablet",
        "country_of_origin": "Kenya",
        "manufacturer": "GlaxoSmithKline Kenya",
        "registration_expiry": "2028-01-10",
    },
    {
        "registration_number": "H2012/00456/002",
        "trade_name": "Amoxil 500mg",
        "active_ingredient": "Amoxicillin",
        "dosage_form": "Capsule",
        "country_of_origin": "Kenya",
        "manufacturer": "Beta Healthcare",
        "registration_expiry": "2027-06-30",
    },
    {
        "registration_number": "H2018/00789/003",
        "trade_name": "Coartem",
        "active_ingredient": "Artemether/Lumefantrine",
        "dosage_form": "Tablet",
        "country_of_origin": "Switzerland",
        "manufacturer": "Novartis",
        "registration_expiry": "2027-09-01",
    },
]

with app.app_context():
    added = 0
    for entry in sample_drugs:
        exists = Drug.query.filter_by(registration_number=entry["registration_number"]).first()
        if not exists:
            drug = Drug(**entry)
            db.session.add(drug)
            added += 1

    db.session.commit()
    print(f"Seeded {added} new drugs (skipped duplicates).")