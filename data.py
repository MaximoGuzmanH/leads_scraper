import pymongo
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import time

# === MongoDB Setup ===
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["procore_scraper"]

# === HTTP Headers (optional, helps avoid blocks) ===
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/91.0.4472.124 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def scrape_single_record(record, counter):
    """
    Scrapes a single Procore record from the DB and updates it back in Mongo.
    """
    collection_name = record["collection_name"]
    collection = db[collection_name]
    business_url = record["url"]
    try:
        response = requests.get(business_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception:
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # === 1) Company Name ===
    h1 = soup.find("h1")
    name = h1.get_text(strip=True) if h1 else "N/A"

    # === 2) Address ===
    addr_a = soup.select_one('a[data-track-click="Business Profile Header, Navigation, Business Address"]')
    address = addr_a.get_text(strip=True) if addr_a else "N/A"

    # === 3) Phone Number ===
    phone_svg = soup.find("svg", attrs={"data-qa": "ci-Phone"})
    phone = phone_svg.find_next("p").get_text(strip=True) if phone_svg and phone_svg.find_next("p") else "N/A"

    # === 4) Company Type ===
    company_type_el = soup.select_one('p[data-test-id="business-profile-nav-about-business-types"]')
    company_type = company_type_el.get_text(strip=True) if company_type_el else "N/A"

    # === 5) Trades and Services ===
    trades_h2 = soup.find("h2", string=lambda txt: txt and "Trades and Services" in txt)
    trades_span = trades_h2.find_next("div").select_one('[data-test-id="expandable-text"] span') if trades_h2 else None
    trades_and_services = trades_span.get_text(strip=True) if trades_span else "N/A"

    # === 6) Market Sectors ===
    market_p = soup.select_one('p[data-test-id="business-profile-nav-about-market-sectors"]')
    market_sectors = market_p.get_text(strip=True) if market_p else "N/A"

    # === Update MongoDB ===
    collection.update_one(
        {"_id": record["_id"]},
        {
            "$set": {
                "name": name,
                "address": address,
                "phone": phone,
                "company_type": company_type,
                "trades_and_services": trades_and_services,
                "market_sectors": market_sectors,
                "status": 1,  # Mark as processed
            }
        },
    )
    counter[0] += 1
    print(f"[INFO] Processed: {business_url} in collection {collection_name} (Total: {counter[0]})")

def scrape_business_data(max_workers=20):
    """
    Fetches all collections and processes records with status=0 in parallel.
    """
    collections = db.list_collection_names()
    all_records = []
    counter = [0]  # Counter to track number of processed records
    
    for col_name in collections:
        collection = db[col_name]
        pending_records = list(collection.find({"status": 0}))
        
        for record in pending_records:
            record["collection_name"] = col_name
        
        all_records.extend(pending_records)
    
    if not all_records:
        print("[INFO] No pending records found in any collection.")
        return

    print(f"[INFO] Processing {len(all_records)} records from all collections.")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(lambda record: scrape_single_record(record, counter), all_records)
    
    print(f"[INFO] Finished processing all collections. Total records processed: {counter[0]}")

if __name__ == "__main__":
    scrape_business_data(max_workers=10)
