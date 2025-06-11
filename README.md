# Stockify

<p align="center">
  <img src="https://github.com/user-attachments/assets/bcfe9f18-ca5e-45d0-a9c5-2b25554782db" alt="Stockify Logo" width="400"/>
</p>

<p align="center">
  A next-generation AI-powered platform for intelligent stock analysis, financial news aggregation, and personalized investment reporting.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#news-scraper">News Scraper</a> •
  <a href="#multi-agent-system">Multi-Agent System</a> •
  <a href="#api-layer">API Layer</a> •

</p>

---

## Features

- 📈 **Real-Time Stock Data**: Fetch historical and real-time data using Yahoo Finance.
- 📊 **Dynamic Visualization**: Interactive candlestick charts with zoom, pan, tooltips, and export options.
- 📰 **News Aggregation**: Collects and analyzes financial news from multiple sources using NLP.
- 🧠 **AI & LLM Integration**: Combines traditional metrics with LLM-powered narrative analysis.
- 🤖 **Multi-Agent System**: Specialized agents handle data analysis, research, and reporting.
- 📄 **Custom Investment Reports**: Automated generation of reports using markdown and PDF export.
- 🌐 **RESTful API**: Built with FastAPI for efficient frontend-backend communication.
- 🧪 **Modular React Frontend**: Includes Stock Reports, Visualization, and News modules.

---

## Architecture

Stockify is structured for modularity and scalability:

- **Frontend**: React.js SPA with modular components.
- **Backend**: FastAPI handles business logic and serves RESTful APIs.
- **Data Layer**: Integrates `yfinance` for stock data and a custom news scraper.
- **Agents**: Multi-agent system synthesizes data into investment-grade reports.
- **LLMs**: Gemini and similar models are used for natural language understanding and summarization.

![System Architecture](https://github.com/user-attachments/assets/fe5db5b1-9aed-41d5-9759-e736d1cff294)

---

## News Scraper

The custom news scraper collects and analyzes market-moving news.

![ News Web Scrapper ](https://github.com/user-attachments/assets/da9a2fed-c65f-41a5-8424-fe0fffb6fa72)



### Key Features

- Aggregates real-time news using Yahoo Finance.
- NLP-based sentiment scoring and entity tagging.
- News relevance ranked against user portfolio.
- External link support for full article access.

---

## Multi-Agent System

Stockify features a distributed multi-agent system to break down complex tasks.

![Multi-Agent System](https://github.com/user-attachments/assets/7ce3c760-eb84-4b75-bc33-b41af07ee3bf)


### Agent Types

- 🧮 **Market Analyst Agent**: Analyzes and ranks stock performance using historical data.
- 🏢 **Company Researcher Agent**: Extracts company profiles, financials, and events.
- 🎯 **Stock Strategist Agent**: Delivers insights and recommendations.
- 🧩 **Team Lead Agent**: Synthesizes insights into coherent, actionable reports.

Each agent runs independently and contributes to a structured investment summary.

---

## API Layer

A robust FastAPI-based backend powers all data flow.

### Main Endpoints
- GET /api/v1/data - Retrieve list of tracked stocks
- GET /api/v1/news - Fetch aggregated and scored news
- GET /api/v1/generate-report - Create investment reports based on agent output

![Main Endpoints](https://github.com/user-attachments/assets/214a77fb-c38b-4466-a882-9eeda061114d)


