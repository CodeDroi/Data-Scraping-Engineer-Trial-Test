import asyncio
import csv
import json
import logging
from playwright.async_api import async_playwright

# --- Configuration & Logging ---
TARGET_URL = "https://scraping-trial-test.vercel.app"
OUTPUT_FILE = "output.json"
LOG_FILE = "scraping_log.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Scraper:
    def __init__(self):
        self.results = []

    async def scrape(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                logging.info(f"Navigating to {TARGET_URL}")
                await page.goto(TARGET_URL, wait_until="networkidle")

                while True:
                    # Parse the current page records
                    await self.extract_page_data(page)

                    # Check for "Next" pagination button
                    next_button = page.locator('button:has-text("Next"), a:has-text("Next")')
                    if await next_button.is_visible() and await next_button.is_enabled():
                        logging.info("Moving to next page...")
                        await next_button.click()
                        await page.wait_for_timeout(1000) # Graceful wait for DOM update
                    else:
                        break

                self.save_data()

            except Exception as e:
                logging.error(f"Critical error during scraping: {e}")
            finally:
                await browser.close()

    async def extract_page_data(self, page):
        # Assuming records are in a table or list of cards
        # Selector '.business-card' is a placeholder for actual site structure
        records = await page.locator('.record-item').all()
        
        for record in records:
            try:
                data = {
                    "business_name": await record.locator('.name').text_content(),
                    "registration_id": await record.locator('.reg-id').text_content(),
                    "status": await record.locator('.status').text_content(),
                    "filing_date": await record.locator('.date').text_content(),
                    "agent_details": {
                        "name": await record.locator('.agent-name').text_content(),
                        "address": await record.locator('.agent-addr').text_content(),
                        "email": await record.locator('.agent-email').text_content(),
                    }
                }
                # Clean whitespace
                cleaned_data = {k: (v.strip() if isinstance(v, str) else v) for k, v in data.items()}
                self.results.append(cleaned_data)
            except Exception as e:
                logging.warning(f"Skipping a record due to missing elements: {e}")

    def save_data(self):
        try:
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(self.results, f, indent=4)
            logging.info(f"Successfully saved {len(self.results)} records to {OUTPUT_FILE}")
        except Exception as e:
            logging.error(f"Failed to save data: {e}")

if __name__ == "__main__":
    scraper = Scraper()
    asyncio.run(scraper.scrape())