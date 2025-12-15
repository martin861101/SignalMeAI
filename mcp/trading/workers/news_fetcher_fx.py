from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import csv
from datetime import datetime, timedelta
import time
import os

BASE_URL = "https://www.forexfactory.com/calendar"


def format_day(date):
    """Convert date to ForexFactory format: monDD.YYYY (e.g., nov17.2025)"""
    return date.strftime("%b").lower() + date.strftime("%d.%Y")


def get_next_7_days():
    """Return list of datetime objects for today + next 6 days (7 days total)"""
    today = datetime.utcnow()
    return [today + timedelta(days=i) for i in range(7)]


def setup_driver():
    """Setup Chromium driver with headless options for terminal"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Use webdriver-manager to automatically get compatible chromedriver for chromium
    try:
        print("  → Setting up Chromium driver...")
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=options)
        print("  ✓ Chromium driver ready")
        return driver
    except Exception as e:
        print(f"  ⚠ Chromium setup failed: {e}")
        print("  → Trying regular Chrome...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("  ✓ Chrome driver ready")
        return driver


def fetch_day(driver, date, retry=0):
    """Fetch USD HIGH IMPACT events only for a given date"""
    day_str = format_day(date)
    url = f"{BASE_URL}?day={day_str}"
    print(f"\nFetching {url} ...")

    try:
        driver.get(url)
    except Exception as e:
        print(f"  ✗ Browser crashed: {e}")
        if retry < 2:
            print(f"  → Retrying (attempt {retry + 1})...")
            time.sleep(5)
            return fetch_day(driver, date, retry + 1)
        else:
            print(f"  ✗ Failed after 3 attempts, skipping this day")
            return []
    
    # Wait for calendar table to load
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "calendar__table"))
        )
        print("  ✓ Calendar table loaded")
        time.sleep(2)
    except Exception as e:
        print(f"  ✗ Error loading page: {e}")
        return []

    events = []
    
    try:
        # Find all calendar rows
        rows = driver.find_elements(By.CSS_SELECTOR, "tr.calendar__row")
        print(f"  → Found {len(rows)} total rows")
        
        usd_high_count = 0
        
        for idx, row in enumerate(rows):
            try:
                # Get impact FIRST - look for the red impact icon
                impact_elements = row.find_elements(By.CSS_SELECTOR, "td.calendar__impact span.icon--ff-impact-red")
                if not impact_elements:
                    # Not high impact, skip this row
                    continue
                
                # Get currency
                currency_elements = row.find_elements(By.CSS_SELECTOR, "td.calendar__currency")
                if not currency_elements:
                    continue
                
                currency = currency_elements[0].text.strip()
                
                # Filter: Only USD
                if currency != "USD":
                    continue
                
                usd_high_count += 1
                
                # Now get other details
                time_elements = row.find_elements(By.CSS_SELECTOR, "td.calendar__time")
                event_elements = row.find_elements(By.CSS_SELECTOR, "td.calendar__event span.calendar__event-title")
                forecast_elements = row.find_elements(By.CSS_SELECTOR, "td.calendar__forecast")
                previous_elements = row.find_elements(By.CSS_SELECTOR, "td.calendar__previous")
                
                event_time = time_elements[0].text.strip() if time_elements else ""
                event_name = event_elements[0].text.strip() if event_elements else ""
                forecast = forecast_elements[0].text.strip() if forecast_elements else ""
                previous = previous_elements[0].text.strip() if previous_elements else ""
                
                events.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "time": event_time,
                    "currency": currency,
                    "impact": "High",
                    "event": event_name,
                    "forecast": forecast,
                    "previous": previous,
                })
                
                print(f"  ✓ USD High Impact: {event_name} at {event_time}")
                
            except Exception as e:
                continue
        
        print(f"  → Extracted {len(events)} USD high-impact events")
        
    except Exception as e:
        print(f"  ✗ Error parsing events: {e}")
    
    return events


def save_to_csv(events, filename="usd_high_impact_next7days.csv"):
    keys = ["date", "time", "currency", "impact", "event", "forecast", "previous"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(events)
    print(f"\n✓ Saved {len(events)} events → {filename}")


if __name__ == "__main__":
    next_7_days = get_next_7_days()
    all_events = []
    
    for date in next_7_days:
        driver = None
        try:
            # Create a fresh driver for each day to avoid crashes
            driver = setup_driver()
            day_events = fetch_day(driver, date)
            all_events.extend(day_events)
            
        except Exception as e:
            print(f"  ✗ Unexpected error for {date.strftime('%Y-%m-%d')}: {e}")
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            time.sleep(3)  # Wait between days

    save_to_csv(all_events)
    print("\n✓ Done! USD High-Impact news for the next 7 days saved.")
