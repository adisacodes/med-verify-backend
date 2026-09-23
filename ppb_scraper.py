"""
PPB Public Drug Register Scraper
---------------------------------
Scrapes the Pharmacy and Poisons Board's public product register
(products.pharmacyboardkenya.org) into a local CSV/JSON dataset for
the counterfeit medicine verification app.

Confirmed via DevTools: the table uses the xCrud PHP library.
Pagination goes through a POST to xcrud_ajax.php with an offset-based
xcrud[start] param (0, 10, 20, ...). Each request also needs xcrud[key]
and xcrud[instance] tokens that are embedded in the main page's HTML
when it first loads (as hidden <input> fields), and these tokens
appear to rotate after each AJAX call.
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import json

BASE_URL = "https://products.pharmacyboardkenya.org/ppb_admin/pages/public_view_retention_products.php"
PAGINATION_URL = "https://products.pharmacyboardkenya.org/ppb_admin/xcrud/xcrud_ajax.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

RESULTS_PER_PAGE = 10

REQUEST_DELAY_SECONDS = 1.5


def extract_xcrud_tokens(html):
    """
    Pull the key/instance values out of a page's HTML.
    They're hidden <input> tags with class="xcrud-data" and
    name="key" / name="instance".
    """
    soup = BeautifulSoup(html, "html.parser")

    key_input = soup.find("input", {"name": "key", "class": "xcrud-data"})
    instance_input = soup.find("input", {"name": "instance", "class": "xcrud-data"})

    key = key_input["value"] if key_input else None
    instance = instance_input["value"] if instance_input else None

    return key, instance


def parse_table(html):
    """Parse a page of the products table into a list of dicts."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")
    records = []

    # First row is the header - grab column names.
    # Strip sort-direction arrows (the currently-sorted column gets a
    # "↓"/"↑" prefix) so field names stay consistent across pages.
    headers = [
        th.get_text(strip=True).lstrip("↓↑").strip()
        for th in rows[0].find_all(["th", "td"])
    ]

    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cells or len(cells) != len(headers):
            continue
        record = dict(zip(headers, cells))
        records.append(record)

    return records


def fetch_page_one(session):
    """
    Fetch and parse the first page, and also extract the key/instance
    tokens needed for the next request.
    Returns (records, key, instance).
    """
    resp = session.get(BASE_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    key, instance = extract_xcrud_tokens(resp.text)
    if not key or not instance:
        raise RuntimeError(
            "Could not find key/instance in the page HTML. The site's "
            "structure may have changed - check View Page Source."
        )

    return parse_table(resp.text), key, instance


def fetch_page_n(session, start_offset, key, instance):
    """
    Fetch a page of results via the xCrud AJAX endpoint.
    start_offset is 0-based: 0 = page 1, 10 = page 2, 20 = page 3, etc.

    Returns (records, next_key, next_instance) - the tokens rotate
    after each request, so we re-extract them from the response and
    use the fresh ones for the following call.
    """
    payload = {
        "xcrud[key]": key,
        "xcrud[orderby]": "tbl_vw_all_items_prims_gbt.registrationdate",
        "xcrud[order]": "desc",
        "xcrud[start]": start_offset,
        "xcrud[limit]": RESULTS_PER_PAGE,
        "xcrud[instance]": instance,
        "xcrud[task]": "list",
        "xcrud[column]": "",
        "xcrud[phrase]": "",
    }

    resp = session.post(PAGINATION_URL, headers=HEADERS, data=payload, timeout=20)
    resp.raise_for_status()

    records = parse_table(resp.text)

    new_key, new_instance = extract_xcrud_tokens(resp.text)
    next_key = new_key or key
    next_instance = new_instance or instance

    return records, next_key, next_instance


def scrape_all(max_pages=323):
    """Scrape all pages and return combined list of drug records."""
    all_records = []
    session = requests.Session()

    print("Fetching page 1 and extracting xcrud tokens...")
    page_one_records, key, instance = fetch_page_one(session)
    all_records.extend(page_one_records)
    print(f"Got tokens - key: {key[:12]}..., instance: {instance[:12]}...")

    for page in range(2, max_pages + 1):
        offset = (page - 1) * RESULTS_PER_PAGE
        print(f"Fetching page {page} (offset {offset})...")
        try:
            records, key, instance = fetch_page_n(session, offset, key, instance)
            if not records:
                print(f"No records on page {page} (offset {offset}) - stopping. "
                      f"If this is well before page {max_pages}, something else "
                      f"is likely wrong (not just end-of-data).")
                break
            all_records.extend(records)
        except requests.RequestException as e:
            print(f"Error on page {page}: {e}")
            break

        time.sleep(REQUEST_DELAY_SECONDS)

    return all_records


def save_to_csv(records, filename="ppb_drug_register.csv"):
    if not records:
        print("No records to save.")
        return
    keys = records[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved {len(records)} records to {filename}")


def save_to_json(records, filename="ppb_drug_register.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(records)} records to {filename}")


if __name__ == "__main__":
    data = scrape_all()
    save_to_csv(data)
    save_to_json(data)