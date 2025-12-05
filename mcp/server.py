from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import httpx
import google.generativeai as genai

# --- Selenium & Scraping Imports ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# Load environment variables
load_dotenv()

# Configuration
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not found in environment variables.")

# Initialize FastAPI
app = FastAPI(title="Learning Research Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# --- Models ---
class SummaryRequest(BaseModel):
    mode: str  # 'topic' or 'url'
    topic: str = ""
    url: str = ""
    email: str = ""

# --- HELPER: Setup Driver ---
def get_selenium_driver():
    """Setup Chromium/Chrome driver with headless options using webdriver-manager"""
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
    
    try:
        # Try Chromium first (common in Linux/Server environments)
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Chromium failed, trying standard Chrome: {e}")
        # Fallback to standard Chrome
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

# --- HELPER: Tavily Search ---
async def search_topic_tavily(topic: str):
    """Uses Tavily to find the best URL for a given topic."""
    if not TAVILY_API_KEY:
        return None, "Tavily API key missing."
    
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": topic,
        "search_depth": "advanced", # Changed to advanced for better research results
        "include_answer": False,
        "max_results": 1
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            data = response.json()
            results = data.get("results", [])
            if results:
                return results[0].get("url"), None
            return None, "No results found."
        except Exception as e:
            return None, str(e)

# --- HELPER: Selenium Scraper ---
def scrape_content(url: str):
    """Scrapes text content from a URL using Selenium."""
    driver = None
    try:
        print(f"Scraping URL: {url}")
        driver = get_selenium_driver()
        driver.get(url)
        driver.implicitly_wait(5)
        
        # Try to get main content first, fall back to body
        try:
            content = driver.find_element(By.TAG_NAME, "main").text
        except:
            content = driver.find_element(By.TAG_NAME, "body").text
            
        # Limit content length to prevent token overflow (approx 15k chars)
        return content[:15000]
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
    finally:
        if driver:
            driver.quit()

# --- HELPER: Gemini Summarization ---
async def generate_learning_summary(raw_text: str, source_topic: str):
    """Uses Gemini to compile a learning-focused summary."""
    if not GEMINI_API_KEY:
        return raw_text + "\n\n[System]: Gemini API Key missing, returning raw scraped text."

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        You are an expert research assistant and teacher. 
        Your goal is to create a comprehensive learning document based on the raw text provided below.
        
        Topic/Context: {source_topic}
        
        Please format the output as follows:
        1. **Executive Summary**: A high-level overview of the core concepts.
        2. **Key Concepts**: Bullet points explaining the most important terms and ideas.
        3. **Detailed Analysis**: A structured explanation of the material.
        4. **Key Takeaways**: What the learner should remember.
        
        Raw Text to Process:
        {raw_text}
        """
        
        # Run in thread to avoid blocking event loop
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary with Gemini: {str(e)}\n\nHere is the raw scraped text instead:\n{raw_text[:2000]}..."

# --- HELPER: Email ---
async def send_email_async(recipient, subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        return "Email credentials not set."
        
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain")) # Gemini output is usually markdown, rendering as plain text for compatibility

        def _send():
            with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)
        
        await asyncio.to_thread(_send)
        return None
    except Exception as e:
        return f"Email failed: {str(e)}"

# --- Routes ---

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Learning Research API is running"}

@app.options("/learning_summary")
async def options_learning_summary():
    return {"status": "ok"}

@app.post("/learning_summary")
async def learning_summary(request: SummaryRequest):
    scraped_content = ""
    source_url = ""
    topic_context = request.topic
    
    # 1. Acquire Data (Search or Direct URL)
    if request.mode == "topic" and request.topic:
        target_url, error = await search_topic_tavily(request.topic)
        if target_url:
            source_url = target_url
            scraped_content = await asyncio.to_thread(scrape_content, target_url)
        else:
            return {"error": f"Could not find topic info: {error or 'Unknown error'}"}

    elif request.mode == "url" and request.url:
        source_url = request.url
        topic_context = f"Content from {request.url}"
        scraped_content = await asyncio.to_thread(scrape_content, request.url)
    
    else:
        raise HTTPException(status_code=400, detail="Please provide a valid topic or URL.")

    if not scraped_content or "Error scraping" in scraped_content:
        return {"error": "Failed to scrape content.", "details": scraped_content}

    # 2. Compile Research (Gemini)
    compiled_research = await generate_learning_summary(scraped_content, topic_context)
    
    # Add Source Metadata
    final_output = f"Research Source: {source_url}\n\n{compiled_research}"

    # 3. Email (Optional)
    if request.email:
        err = await send_email_async(request.email, f"Research: {topic_context}", final_output)
        if err:
            final_output += f"\n\n[System Warning]: Email failed to send ({err})"
        else:
            final_output += f"\n\n[System]: Copy sent to {request.email}"

    return {"summary": final_output, "source_url": source_url}

if __name__ == "__main__":
    import socket
    def get_network_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Unable to determine"
    
    local_ip = get_network_ip()
    print("=" * 50)
    print(f"Server running at: http://{local_ip}:8000")
    print("=" * 50)
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)