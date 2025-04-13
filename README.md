# NewsWhat - Funny AI News Translator

A Flask web application that automatically crawls news articles from sources like CNN, and uses AI models via g4f to generate humorous translations, summaries, and analysis on demand.

## Features

- Web scraping of CNN headlines and article content
- On-demand AI-powered processing with multiple features:
  - Humorous, simplified translations of complex news
  - Concise summaries of articles
  - Topic categorization and sentiment analysis
  - Key entity extraction
  - Core points highlighted with markdown formatting
- Responsive UI for browsing news and viewing detailed analyses
- Debug page to monitor AI service status

## How It Works

1. The application crawls CNN's website for recent headlines
2. When a user clicks on an article, the application:
   - Extracts the full article content
   - Sends it to available AI models for analysis
   - Displays a detailed view with the funny translation, summary, and other analysis
3. The app attempts to use various AI models through g4f, with automatic fallbacks

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
5. Visit the Debug page to see information about available AI services

## Data Storage

The application stores crawled articles and their AI-generated content in a local `articles.json` file. This serves as a simple database and persists between application restarts.

## Note on Web Scraping

This application performs web scraping on CNN's website. Please note that CNN's page structure may change over time, which could affect the scraping functionality. The selectors in the code may need occasional updates.

## Dependencies

- Flask - Web framework
- Requests - HTTP requests
- BeautifulSoup4 - HTML parsing
- g4f - API for accessing various AI models
- Marked.js - For rendering markdown in the browser

## Disclaimer

This application is for educational purposes only. Always respect the terms of service of websites you interact with.

The g4f library provides unofficial access to AI models and may have limitations:
- Service availability may be inconsistent
- Quality of responses may vary
- The library may stop working if providers change their APIs

Use responsibly and be aware of potential legal and ethical considerations when using unofficial API access methods. 