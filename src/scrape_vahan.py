# src/scrape_vahan.py
"""
Selenium scraper for Vahan Dashboard (vehicle type & manufacturer registrations).
Saves CSV to ../data/raw_vahan.csv with columns: date, manufacturer, vehicle_type, registrations, period
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from pathlib import Path

BASE_URL = "https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml"
OUT_PATH = Path(__file__).resolve().parents[1] / 'data' / 'raw_vahan.csv'
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_driver(headless=False):
    """Initialize Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_for(selector, driver, by=By.CSS_SELECTOR, timeout=15):
    """Wait for element to appear."""
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))

def get_table_rows(driver, table_selector="table"):
    """Reads table rows from the page."""
    rows = driver.find_elements(By.CSS_SELECTOR, f"{table_selector} tbody tr")
    parsed = []
    for r in rows:
        cols = r.find_elements(By.TAG_NAME, "td")
        if not cols:
            continue
        values = [c.text.strip() for c in cols]
        parsed.append(values)
    return parsed

def parse_rows_to_df(rows):
    """Parses raw rows into DataFrame."""
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    if df.shape[1] >= 5:
        df = df.iloc[:, :5]
        df.columns = ["sno", "manufacturer", "vehicle_type", "registrations", "period"]
        df['registrations'] = df['registrations'].str.replace(',', '').str.extract(r"(\d+)")
        df['registrations'] = pd.to_numeric(df['registrations'], errors='coerce')
        return df[['manufacturer', 'vehicle_type', 'registrations', 'period']]
    else:
        return pd.DataFrame(rows)

def main():
    print("[INFO] Starting scraper...")
    driver = init_driver(headless=False)
    print(f"[INFO] Opening {BASE_URL}")
    driver.get(BASE_URL)

    time.sleep(5)  # Wait for page to load

    try:
        print("[INFO] Waiting for table...")
        wait_for("table", driver, By.CSS_SELECTOR, timeout=15)
    except:
        print("[WARNING] Table not found automatically.")

    print("[INFO] Reading table rows...")
    rows = get_table_rows(driver)

    df = parse_rows_to_df(rows)
    if df.empty:
        print("[WARNING] No rows found. Saving page snapshot for debugging...")
        with open(OUT_PATH.parent / 'page_snapshot.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
    else:
        df.to_csv(OUT_PATH, index=False)
        print(f"[SUCCESS] Data saved to {OUT_PATH}")

    # Keep browser open for inspection
    print("\n[DEBUG] Browser will remain open. Inspect the page.")
    input("Press Enter here to close browser and finish...")
    driver.quit()
    print("[INFO] Scraper finished.")

if __name__ == '__main__':
    main()
