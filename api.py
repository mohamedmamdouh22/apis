import asyncio
import logging
import httpx
from datetime import datetime
from fastapi import FastAPI
from parsel import Selector

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("fetch_bids.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)
app = FastAPI()
stock_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))

async def scrape_trends():
    """Scrapes trending stock data from Yahoo Finance"""
    logger.info("Trendings: scraping data")
    response = await stock_client.get("https://www.investing.com/equities/egypt")
    sel = Selector(response.text)
    parsed = []

    rows = sel.css('div[data-test="dynamic-table"] table tbody tr')
    logger.debug(f"Found {len(rows)} rows")

    for i, row in enumerate(rows):
        name = row.css("td:nth-child(2)  a > h4 >span >span:last-child::text").get()
        last = row.css("td:nth-child(3) span::text").get()
        high = row.css("td:nth-child(4)::text").get()
        low = row.css("td:nth-child(5)::text").get()
        chg = row.css("td:nth-child(6)::text").get()
        chg_percentage = row.css("td:nth-child(7)::text").get()
        volume = row.css("td:nth-child(8)::text").get()
        if name:
            item = {
                "Company Name": name,
                "Last Price": last,
                "Highest Price": high,
                "Lowest Price": low,
                "Change in price": chg,
                "% change": chg_percentage,
                "Volume": volume,
            }
            logger.debug(f"Row {i}: {item}")
            parsed.append(item)
        else:
            logger.warning(f"Row {i} has no symbol")

    parsed.append({"_scraped_on": datetime.now()})
    return parsed




@app.get("/")
async def scrape_trend():
    return await scrape_trends()

@app.on_event("startup")
async def app_startup():
    global stock_client
    stock_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))

@app.on_event("shutdown")
async def app_shutdown():
    await stock_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
#uvicorn api:app --reload