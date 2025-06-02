from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging

from Graphs.utils import getCandlestickChartData
from Report.report import get_final_investment_report
from news.news import YahooFinanceStockNewsScraper

import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scraper instance
scraper = YahooFinanceStockNewsScraper()

# ----------- Pydantic Models -----------

class SymbolsRequest(BaseModel):
    symbols: List[str]

class StockRequest(BaseModel):
    stock: str

class NewsRequest(BaseModel):
    max_articles: Optional[int] = 10

# ----------- Endpoints -----------

@app.post("/generate_report")
async def generate_report(payload: SymbolsRequest):
    try:
        symbols = [s.strip().upper() for s in payload.symbols if isinstance(s, str) and s.strip()]
        if not symbols:
            raise HTTPException(status_code=400, detail="Provide a non-empty list of valid stock symbols.")
        
        logger.info(f"Generating report for symbols: {symbols}")
        report = get_final_investment_report(symbols)
        
        return {
            "status": "success",
            "symbols": symbols,
            "report": report
        }

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        status_code = 429 if "Rate limited" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


@app.post("/data")
async def get_stock_data(payload: StockRequest):
    ticker = payload.stock.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Stock ticker cannot be empty.")

    try:
        historical_data = getCandlestickChartData(ticker)
        if historical_data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")

        historical_data = historical_data.reset_index().to_dict(orient="records")
        return historical_data

    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching data for {ticker}: {str(e)}")


@app.post("/update-news")
async def update_news(payload: NewsRequest):
    try:
        max_articles = payload.max_articles or 10
        articles = scraper.get_stock_news_articles(max_articles=max_articles, recent_only=True)
        return {
            "status": "success",
            "count": len(articles),
            "articles": articles
        }
    except Exception as e:
        logger.error(f"Error updating news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/health")
async def health_check():
    try:
        # Simple health check to ensure the app is running
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")