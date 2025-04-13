# NewsWhat - AI News Summarizer

A Flask web application that automatically crawls news articles from sources like CNN, and uses the Claude 3.7 Sonnet model via g4f to generate summaries and analysis on demand.

## Features

- Web scraping of CNN headlines and article content
- On-demand AI-powered summarization and analysis using Claude 3.7 Sonnet
- Topic categorization and sentiment analysis
- Key entity extraction
- Clean, responsive UI for browsing news and viewing detailed analyses

## How It Works

1. The application crawls CNN's website for recent headlines
2. When a user clicks on an article, the application:
   - Extracts the full article content
   - Sends it to available AI models for analysis
   - Displays a detailed view with summary, topic, sentiment, and key entities

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python app.py
   ```
2. Open your browser and navigate to `http://127.0.0.1:5000`
3. Click "Crawl Latest News" to fetch current headlines
4. Click on any article card to view or generate its AI analysis

## Note on Web Scraping

This application performs web scraping on CNN's website. Please note that CNN's page structure may change over time, which could affect the scraping functionality. The selectors in the code may need occasional updates.

## Dependencies

- Flask - Web framework
- Requests - HTTP requests
- BeautifulSoup4 - HTML parsing
- g4f - API for accessing Claude 3.7 Sonnet
- Python-dateutil - Date parsing utilities

## Disclaimer

This application is for educational purposes only. Always respect the terms of service of websites you interact with. The use of Claude 3.7 Sonnet through g4f may be subject to specific terms and conditions. 