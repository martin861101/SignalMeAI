import os
import time
import json
import re
import dotenv
from tavily import TavilyClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# --- Load environment variables ---
dotenv.load_dotenv()

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
MISTRAL_API_KEY  = os.getenv("MISTRAL_API_KEY")
TAVILY_API_KEY   = os.getenv("TAVILY_API_KEY")


# --- Helper function ---
def safe_parse_analysis(raw_output: str) -> dict:
    """Parse AI JSON output safely."""
    if not raw_output:
        return {}
    cleaned = re.sub(r"^```json\s*|```$", "", raw_output.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing failed: {e}")
        return {}


# --- Research Tools ---
class ResearchTools:
    def __init__(self, tavily_api_key=None):
        api_key = tavily_api_key or TAVILY_API_KEY
        self.tavily_client = TavilyClient(api_key=api_key) if api_key else None
        self.driver = self._setup_driver()

    def _setup_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        try:
            try:
                driver = webdriver.Chrome(options=options)
            except:
                options.binary_location = "/usr/bin/chromium-browser"
                driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            print(f"Web driver setup failed: {e}")
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def search_web(self, query: str, max_results: int = 5) -> list:
        if self.tavily_client:
            try:
                response = self.tavily_client.search(
                    query=query,
                    max_results=max_results,
                    search_depth="advanced"
                )
                urls = [result['url'] for result in response.get('results', [])[:max_results]]
                print(f"Found {len(urls)} URLs")
                return urls
            except Exception as e:
                print(f"Tavily search failed: {e}")
        # Fallback URLs
        return [
            f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            f"https://example.com/about-{query.lower().replace(' ', '-')}",
            f"https://news.ycombinator.com/search?q={query.replace(' ', '+')}"
        ]

    def scrape_content(self, urls: list, max_length: int = 3000) -> dict:
        if not self.driver:
            print("No web driver available")
            return {"error": "Web driver not available"}
        
        scraped_data = {}
        for i, url in enumerate(urls[:5]):
            try:
                print(f"Scraping {i+1}/{len(urls)}: {url}")
                self.driver.get(url)
                time.sleep(2)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                for script in soup(["script", "style"]):
                    script.decompose()
                paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'article'])
                text = ' '.join([elem.get_text().strip() for elem in paragraphs if elem.get_text().strip()])
                text = text[:max_length] + "..." if len(text) > max_length else text
                scraped_data[url] = text
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                scraped_data[url] = f"Failed to scrape: {str(e)}"
        return scraped_data

    def cleanup(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
