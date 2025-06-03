import os
import yfinance as yf
from agno.agent import Agent
from agno.models.google import Gemini
import time
from google.api_core.exceptions import TooManyRequests
import logging
import pandas as pd
import asyncio
import concurrent.futures
from threading import Lock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variable for Google API
os.environ["GOOGLE_API_KEY"] = "AIzaSyDdtq0l5VfOLUi7wSlH3IddSwwSkoyX5nM"

# Thread lock for shared resources
data_lock = Lock()

def compare_stocks(symbols):
    try:
        logger.info(f"Downloading stock data for: {symbols}")
        data = yf.download(symbols, period="6mo", group_by="ticker")
        result = []

        for symbol in symbols:
            try:
                if len(symbols) == 1:
                    # Single stock case
                    close_prices = data['Close'].dropna()
                else:
                    # Multiple stocks case
                    if symbol in data.columns.levels[0]:
                        close_prices = data[symbol]['Close'].dropna()
                    else:
                        logger.warning(f"No data found for {symbol}")
                        continue
                
                if not close_prices.empty and len(close_prices) > 1:
                    initial = (close_prices[1] - close_prices[0]) / close_prices[0]
                    total = close_prices.pct_change().sum()
                    result.append({
                        "Symbol": symbol,
                        "Initial % Change": round(initial * 100, 2),  # Convert to percentage
                        "6-Month % Change": round(total * 100, 2)     # Convert to percentage
                    })
                    logger.info(f"Data processed for {symbol}")
                else:
                    logger.warning(f"Insufficient data for {symbol}")
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        return pd.DataFrame(result).set_index("Symbol") if result else pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

# Market Analyst Agent
market_analyst = Agent(
    model=Gemini(id="models/gemini-2.0-flash-001"),
    description="Analyzes and compares stock performance over time.",
    show_tool_calls=True,
    markdown=True
)

def get_market_analysis(symbols):
    try:
        logger.info(f"Starting market analysis for symbols: {symbols}")
        performance_data = compare_stocks(symbols)
        
        if performance_data.empty:
            logger.warning("No valid stock data found.")
            return "No valid stock data found for the given symbols."
        
        # Format as markdown table
        formatted_table = performance_data.to_markdown()
        logger.info(f"Performance data table:\n{formatted_table}")

        prompt = (
            "You are a professional equity analyst. Analyze the stock performance data below.\n\n"
            f"Stock Performance Data (6-month period):\n{formatted_table}\n\n"
            "Tasks:\n"
            "1. Compare and rank these stocks from best to worst performing\n"
            "2. Use the specific percentage numbers in your analysis\n"
            "3. Explain your ranking rationale clearly\n"
            "4. Keep your response concise and data-driven\n\n"
            "Provide a clear, professional analysis."
        )

        logger.info("Calling market analyst agent...")
        analysis = market_analyst.run(prompt)
        logger.info("Market analysis completed")
        return str(analysis.content)

    except Exception as e:
        logger.error(f"Error in market analysis: {str(e)}")
        return f"Error in market analysis: {str(e)}"

# Company Researcher Functions
def get_company_info(symbol):
    try:
        logger.info(f"Fetching company info for {symbol}")
        stock = yf.Ticker(symbol)
        time.sleep(0.5)
        info = stock.get_info()
        return {
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "summary": info.get("longBusinessSummary", "N/A")[:500] + "..." if info.get("longBusinessSummary") else "N/A",  # Truncate summary
        }
    except Exception as e:
        logger.error(f"Error fetching company info for {symbol}: {str(e)}")
        return {
            "name": "N/A",
            "sector": "N/A", 
            "market_cap": "N/A",
            "summary": "N/A"
        }

def get_company_news(symbol):
    try:
        logger.info(f"Fetching news for {symbol}")
        stock = yf.Ticker(symbol)
        news = stock.news[:3]  # Limit to 3 news items
        time.sleep(0.5)
        return news
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {str(e)}")
        return []

company_researcher = Agent(
    model=Gemini(id="models/gemini-2.0-flash-001"),
    description="Fetches company profiles, financials, and latest news.",
    markdown=True
)

def get_company_analysis(symbol):
    try:
        logger.info(f"Starting company analysis for {symbol}")
        info = get_company_info(symbol)
        news = get_company_news(symbol)
        
        # Limit news content to prevent recursion
        news_summary = []
        for item in news[:2]:  # Only take first 2 news items
            if isinstance(item, dict) and 'title' in item:
                news_summary.append(item['title'])
        
        prompt = (
            f"Provide a company analysis for {symbol}.\n"
            f"Company: {info['name']}\n"
            f"Sector: {info['sector']}\n"
            f"Market Cap: {info['market_cap']}\n"
            f"Business Summary: {info['summary']}\n"
            f"Recent News Headlines: {'; '.join(news_summary[:2])}\n\n"
            f"Provide a concise analysis covering business overview, sector position, and recent developments."
        )
        
        logger.info(f"Calling company researcher for {symbol}...")
        response = company_researcher.run(prompt)
        logger.info(f"Company analysis completed for {symbol}")
        return str(response.content)
    
    except Exception as e:
        logger.error(f"Error in company analysis for {symbol}: {str(e)}")
        return f"Error analyzing {symbol}: {str(e)}"

def get_all_company_analyses(symbols):
    """Get company analyses for all symbols in parallel"""
    try:
        logger.info(f"Starting parallel company analyses for {symbols}")
        
        # Use ThreadPoolExecutor to run company analyses in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(symbols), 5)) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(get_company_analysis, symbol): symbol 
                for symbol in symbols
            }
            
            # Collect results
            company_analyses = {}
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    analysis = future.result(timeout=60)  # 60 second timeout per analysis
                    company_analyses[symbol] = analysis
                    logger.info(f"Company analysis completed for {symbol}")
                except Exception as e:
                    logger.error(f"Error in company analysis for {symbol}: {str(e)}")
                    company_analyses[symbol] = f"Error analyzing {symbol}: {str(e)}"
        
        return company_analyses
    
    except Exception as e:
        logger.error(f"Error in parallel company analyses: {str(e)}")
        return {symbol: f"Error analyzing {symbol}: {str(e)}" for symbol in symbols}

# Stock Strategist Agent
stock_strategist = Agent(
    model=Gemini(id="models/gemini-2.0-flash-001"),
    description="Provides investment insights and recommends top stocks.",
    markdown=True
)

def get_stock_recommendations(symbols, market_analysis=None, company_data=None):
    try:
        logger.info(f"Starting stock recommendations for {symbols}")
        
        # Use provided data or get fresh data (for backwards compatibility)
        if market_analysis is None:
            market_analysis = get_market_analysis(symbols)
        
        if company_data is None:
            company_data = get_all_company_analyses(symbols)
        
        prompt = (
            f"Based on the following analysis, provide investment recommendations for these stocks: {', '.join(symbols)}\n\n"
            f"Market Performance Analysis:\n{market_analysis[:1000]}...\n\n"  # Truncate to prevent recursion
            f"Company Analysis Summary:\n"
        )
        
        # Add truncated company analyses
        for symbol, analysis in company_data.items():
            prompt += f"{symbol}: {analysis[:300]}...\n"
        
        prompt += (
            f"\nProvide:\n"
            f"1. Investment recommendation for each stock\n"
            f"2. Risk assessment\n"
            f"3. Your top pick and reasoning\n"
            f"Keep response concise and actionable."
        )
        
        logger.info("Calling stock strategist...")
        recommendations = stock_strategist.run(prompt)
        logger.info("Stock recommendations completed")
        return str(recommendations.content)
    
    except Exception as e:
        logger.error(f"Error in stock recommendations: {str(e)}")
        return f"Error generating recommendations: {str(e)}"

# Parallel execution function
def run_agents_in_parallel(symbols):
    """Run market analysis, company research, and stock strategist in parallel"""
    try:
        logger.info(f"Starting parallel execution for {symbols}")
        
        # Results dictionary to store outputs
        results = {}
        
        # Use ThreadPoolExecutor to run the three main tasks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit the three main tasks
            market_future = executor.submit(get_market_analysis, symbols)
            company_future = executor.submit(get_all_company_analyses, symbols)
            
            # Wait for market analysis and company data to complete
            # before starting stock recommendations (since it depends on both)
            market_analysis = market_future.result(timeout=120)  # 2 minutes timeout
            company_data = company_future.result(timeout=180)    # 3 minutes timeout
            
            # Now run stock recommendations with the completed data
            recommendations_future = executor.submit(
                get_stock_recommendations, 
                symbols, 
                market_analysis, 
                company_data
            )
            
            # Collect final result
            stock_recommendations = recommendations_future.result(timeout=120)  # 2 minutes timeout
            
            results = {
                'market_analysis': market_analysis,
                'company_data': company_data,
                'stock_recommendations': stock_recommendations
            }
        
        logger.info("Parallel execution completed successfully")
        return results
    
    except concurrent.futures.TimeoutError:
        logger.error("Timeout occurred during parallel execution")
        return {
            'market_analysis': "Timeout error in market analysis",
            'company_data': {symbol: f"Timeout error for {symbol}" for symbol in symbols},
            'stock_recommendations': "Timeout error in stock recommendations"
        }
    except Exception as e:
        logger.error(f"Error in parallel execution: {str(e)}")
        return {
            'market_analysis': f"Error in market analysis: {str(e)}",
            'company_data': {symbol: f"Error analyzing {symbol}: {str(e)}" for symbol in symbols},
            'stock_recommendations': f"Error in recommendations: {str(e)}"
        }

# Team Lead Agent
team_lead = Agent(
    model=Gemini(id="gemini-2.0-flash-001"),
    description="Aggregates stock analysis, company research, and investment strategy.",
    instructions=[
        "Create a structured investment report with 4 sections",
        "Present information clearly and concisely",
        "Focus on actionable insights"
    ],
    markdown=True
)

def get_final_investment_report(symbols):
    try:
        logger.info(f"Starting final report generation for {symbols}")
        
        # Run all agents in parallel
        parallel_results = run_agents_in_parallel(symbols)
        
        # Extract results
        market_analysis = parallel_results['market_analysis']
        company_data = parallel_results['company_data']
        stock_recommendations = parallel_results['stock_recommendations']
        
        logger.info("All parallel analyses completed")
        
        # Format company analyses
        company_analyses = []
        for symbol, analysis in company_data.items():
            company_analyses.append(f"**{symbol}**: {analysis}")

        # Create the complete report by combining all sections
        complete_report = f"""# Stock Investment Report for {', '.join(symbols)}

## Section 1: Market Performance Overview
{market_analysis}

## Section 2: Company Fundamentals and Sector Overview
{chr(10).join(company_analyses)}

## Section 3: Investment Recommendations
{stock_recommendations}

## Section 4: Investment Opportunities Summary

Based on the comprehensive analysis above, here is the investment ranking:

| Stock Ticker | Investment Score (1-10) | Rationale |
|--------------|-------------------------|-----------|"""

        # Let the team lead only create the summary table
        table_prompt = (
            f"Based on the following complete analysis, create ONLY the summary table rows for the investment ranking.\n\n"
            f"Market Analysis: {market_analysis[:500]}...\n\n"
            f"Company Data: {str(list(company_data.values()))[:500]}...\n\n"
            f"Recommendations: {stock_recommendations[:500]}...\n\n"
            f"For each stock ({', '.join(symbols)}), provide one table row with:\n"
            f"- Stock ticker\n"
            f"- Investment score (1-10, where 1=Strong Buy, 10=Strong Sell)\n"
            f"- Brief rationale (one sentence)\n\n"
            f"Format as: | TICKER | SCORE | Rationale |\n"
            f"Provide ONLY the table rows, no headers or extra text."
        )

        logger.info("Calling team lead for summary table...")
        table_rows = team_lead.run(table_prompt)
        
        # Combine the complete report with the table
        final_report = complete_report + "\n" + str(table_rows.content) + "\n\n**Disclaimer:** This analysis is for informational purposes only and should not be considered as financial advice. Please consult with a qualified financial advisor before making investment decisions."
        
        logger.info("Final report generation completed")
        return final_report
    
    except Exception as e:
        logger.error(f"Error generating final report: {str(e)}")
        return f"Error generating final investment report: {str(e)}"

# Utility function to run analysis with timing
def analyze_stocks_with_timing(symbols):
    """Wrapper function that includes timing information"""
    start_time = time.time()
    
    logger.info(f"Starting stock analysis for: {symbols}")
    logger.info("=" * 50)
    
    try:
        report = get_final_investment_report(symbols)
        
        end_time = time.time()
        execution_time = round(end_time - start_time, 2)
        
        logger.info("=" * 50)
        logger.info(f"Analysis completed in {execution_time} seconds")
        
        return f"{report}\n\n---\n**Execution Time:** {execution_time} seconds (with parallel processing)"
        
    except Exception as e:
        end_time = time.time()
        execution_time = round(end_time - start_time, 2)
        logger.error(f"Analysis failed after {execution_time} seconds: {str(e)}")
        return f"Analysis failed: {str(e)}"

