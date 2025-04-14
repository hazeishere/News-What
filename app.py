from flask import Flask, render_template, request, redirect, url_for
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import json
from urllib.parse import urlparse
import traceback
import re
import g4f
import random

# Global variables for tracking
LAST_USED_MODEL = "Unknown"
AVAILABLE_MODELS = []
USE_G4F_CLIENT = False
USE_G4F_LEGACY = False

try:
    from g4f.client import Client
    USE_G4F_CLIENT = True
    client = Client()
        
except (ImportError, Exception) as e:
    print(f"g4f client not available: {e}")
    USE_G4F_CLIENT = False
    try:
        # Try legacy g4f interface
        USE_G4F_LEGACY = True
        print(f"Using legacy g4f interface")
            
    except (ImportError, Exception) as e:
        print(f"Legacy g4f not available: {e}")
        USE_G4F_LEGACY = False

app = Flask(__name__)

# Helper function to get available models
def get_available_g4f_models():
    models = []

    # Add some default models that usually work
    default_models = ["claude-3.7-sonnet", "gemini-2.0-flash", "gpt-4o-mini"]
    for model in default_models:
        if model not in models:
            models.append(model)
      
    return models

# Store crawled articles
class ArticleStore:
    def __init__(self, storage_file="articles.json"):
        self.storage_file = storage_file
        self.articles = self._load_articles()
    
    def _load_articles(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_articles(self):
        with open(self.storage_file, "w") as f:
            json.dump(self.articles, f)
    
    def add_article(self, article):
        self.articles.append(article)
        self.save_articles()
    
    def get_articles(self):
        return sorted(self.articles, key=lambda x: x.get('crawled_at', ''), reverse=True)
    
    def get_article_by_id(self, article_id):
        for article in self.articles:
            if article.get('id') == article_id:
                return article
        return None
        
    def update_article(self, article_id, updates):
        for i, article in enumerate(self.articles):
            if article.get('id') == article_id:
                self.articles[i].update(updates)
                self.save_articles()
                return True
        return False

# Initialize article store
article_store = ArticleStore()

def crawl_cnn_headlines():
    url = "https://www.cnn.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        all_headlines = []
        
        # Get headline articles from CNN homepage using span elements
        # Note: CNN's page structure may change, so this selector might need updates
        for headline_span in soup.select('span.container__headline-text[data-editable="headline"]'):
            headline = headline_span.text.strip()
            
            # Find the closest parent <a> tag to get the link
            parent_link = headline_span.find_parent('a')
            link = parent_link.get('href') if parent_link else None
            
            # Handle relative URLs
            if link and not link.startswith(('http://', 'https://')):
                link = f"https://www.cnn.com{link}"
                
            # Generate article ID from URL
            article_id = str(abs(hash(link)))[-10:] if link else None
                
            if headline and link and article_id and not any(a.get('url') == link for a in article_store.articles):
                all_headlines.append({
                    'title': headline,
                    'url': link,
                    'id': article_id
                })
        
        # Randomly select up to 9 articles
        if all_headlines:
            selected_headlines = random.sample(all_headlines, min(9, len(all_headlines)))
            return selected_headlines
        return []
    except Exception as e:
        print(f"Error crawling CNN: {e}")
        return []

def extract_article_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('h1')
        title = title.text if title else "No title found"
        
        # Extract content paragraphs (CNN specific - may need adjustments)
        paragraphs = soup.select('.paragraph')
        content = ' '.join([p.text for p in paragraphs])
        
        if not content:
            # Fallback to generic paragraph extraction
            paragraphs = soup.find_all('p')
            content = ' '.join([p.text for p in paragraphs])
        
        return {
            'title': title,
            'content': content[:8000]  # Limit content length
        }
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return {'title': 'Error', 'content': f'Failed to extract content: {str(e)}'}

def analyze_with_claude(title, content):
    global USE_G4F_CLIENT, USE_G4F_LEGACY, LAST_USED_MODEL, AVAILABLE_MODELS
    
    prompt = f"""
    You are a professional news summarizer and analyst with a great sense of humor. Below is a news article.
    Title: {title}
    
    Content: {content}
    
    Please provide:
    1. A funny translation of the news article that makes it easier to understand and more humorous (200-500 characters)
    2. A concise 3-5 sentence summary of the article
    3. The main topic category (politics, technology, health, etc.)
    4. Overall sentiment (positive, negative, or neutral)
    5. Key entities mentioned (people, organizations, locations)
    6. Core points of the article formatted in markdown, with 3-5 bullet points highlighting the most important information
    
    Format your response as JSON with the following structure:
    {{
        "funny_translation": "your humorous simplified version here",
        "summary": "your summary here",
        "topic": "main topic",
        "sentiment": "sentiment",
        "key_entities": ["entity1", "entity2", "entity3"],
        "core_points_markdown": "- First key point\\n- Second key point\\n- Third key point"
    }}
    """
    
    try:
        response_text = ""
        
        # Get available models
        available_models = get_available_g4f_models()
        AVAILABLE_MODELS = available_models  # Update global list
        
        # Find the best available model
        selected_model = None
        for model in available_models:
            if any(model in avail_model for avail_model in available_models):
                selected_model = next((avail_model for avail_model in available_models if model in avail_model), None)
                break
        
        if not selected_model and available_models:
            selected_model = available_models[0]  # Use first available
        
        print(f"Selected model: {selected_model}")
        LAST_USED_MODEL = selected_model  # Update global tracking
        
        # Try g4f client if available
        if USE_G4F_CLIENT:
            try:
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Handle different response formats
                if hasattr(response, 'choices') and response.choices:
                    response_text = response.choices[0].message.content
                else:
                    response_text = str(response)

                print("Used g4f client successfully")
            except Exception as e:
                print(f"g4f client error: {e}")
                USE_G4F_CLIENT = False  # Disable for next calls
        
        # Try legacy g4f as fallback
        if not response_text and USE_G4F_LEGACY:
            try:
                response_text = g4f.ChatCompletion.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": prompt}],
                )
                print("Used legacy g4f successfully")
            except Exception as e:
                print(f"Legacy g4f error: {e}")
                USE_G4F_LEGACY = False  # Disable for next calls
        
        # If all methods failed, create a fallback response
        if not response_text:
            print("All g4f methods failed, using fallback")
            return {
                "summary": f"Failed to generate summary for '{title}'. Unable to connect to AI services.",
                "topic": "Unknown",
                "sentiment": "Neutral",
                "key_entities": [],
                "core_points_markdown": ""
            }
        
        print(f"AI Response: {response_text}...")
        
        # Try to parse JSON response
        try:
            # Check if the response is already a valid JSON string
            if isinstance(response_text, str):
                # Sometimes the response might be cut off or contain additional text
                # Try to find valid JSON within the response
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    try:
                        result = json.loads(json_str)
                        # Verify all required fields are present
                        required_fields = ['summary', 'topic', 'sentiment', 'key_entities']
                        if all(field in result for field in required_fields):
                            return result
                    except:
                        pass  # Continue to next approach if this fails
                
                # Direct parsing approach
                try:
                    result = json.loads(response_text)
                    return result
                except:
                    pass  # Continue to fallback if this fails
            
            # If the response is already a Python dict, use it directly
            elif isinstance(response_text, dict):
                return response_text
                
            # Fallback: Extract content as best we can using regex patterns
            summary_match = re.search(r'"summary":\s*"([^"]*)"', response_text, re.DOTALL)
            topic_match = re.search(r'"topic":\s*"([^"]*)"', response_text, re.DOTALL)
            sentiment_match = re.search(r'"sentiment":\s*"([^"]*)"', response_text, re.DOTALL)
            funny_match = re.search(r'"funny_translation":\s*"([^"]*)"', response_text, re.DOTALL)
            
            # Create a fallback result dictionary
            result = {
                "summary": summary_match.group(1) if summary_match else response_text[:500],
                "topic": topic_match.group(1) if topic_match else "Unknown",
                "sentiment": sentiment_match.group(1) if sentiment_match else "Unknown",
                "funny_translation": funny_match.group(1) if funny_match else "",
                "key_entities": [],
                "core_points_markdown": ""
            }
            
            return result
            
        except json.JSONDecodeError:
            # Extract what we can from the response
            print(f"JSONDecodeError with response: {response_text[:100]}...")
            
            # Fallback if response is not valid JSON
            return {
                "summary": response_text[:500] if response_text else "No summary available",
                "topic": "Unknown",
                "sentiment": "Unknown",
                "key_entities": [],
                "funny_translation": "",
                "core_points_markdown": ""
            }
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error using g4f: {e}")
        print(f"Detailed error: {error_details}")
        return {
            "summary": f"Failed to generate summary. Error: {str(e)[:100]}...",
            "topic": "Error",
            "sentiment": "Unknown",
            "key_entities": [],
            "core_points_markdown": ""
        }

@app.route('/')
def home():
    articles = article_store.get_articles()
    return render_template('index.html', articles=articles)

@app.route('/article/<article_id>')
def view_article(article_id):
    article = article_store.get_article_by_id(article_id)
    
    if not article:
        return redirect(url_for('home'))
    
    # Generate summary only if not already done
    if not article.get('has_summary', False):
        article_data = extract_article_content(article['url'])
        
        if article_data['content']:
            analysis = analyze_with_claude(article_data['title'], article_data['content'])
            
            # Helper function to sanitize text fields
            def sanitize_text(text, max_length=3000):
                if not text:
                    return ""
                # Remove any control characters and limit length
                clean_text = ''.join(c for c in text if c.isprintable() or c in ['\n', '\t'])
                return clean_text[:max_length]
            
            # Update article with summary data
            updates = {
                'summary': sanitize_text(analysis.get('summary', 'No summary available')),
                'funny_translation': sanitize_text(analysis.get('funny_translation', 'No funny translation available')),
                'topic': sanitize_text(analysis.get('topic', 'Unknown'), 50),
                'sentiment': sanitize_text(analysis.get('sentiment', 'Unknown'), 20),
                'key_entities': analysis.get('key_entities', [])[:15],  # Limit to 15 entities
                'core_points_markdown': sanitize_text(analysis.get('core_points_markdown', '')),
                'has_summary': True
            }
            
            article_store.update_article(article_id, updates)
            article = article_store.get_article_by_id(article_id)
    
    return render_template('article.html', article=article)

@app.route('/crawl', methods=['POST'])
def crawl():
    headlines = crawl_cnn_headlines()
    
    for headline in headlines:
        try:
            article_data = extract_article_content(headline['url'])
            
            # Store the article without summary initially
            article = {
                'id': headline['id'],  # Use the ID from headline
                'title': article_data['title'],
                'url': headline['url'],
                'domain': urlparse(headline['url']).netloc,
                'has_summary': False,
                'summary': "Click to generate summary",
                'topic': "Unknown",
                'sentiment': "Unknown",
                'key_entities': [],
                'crawled_at': datetime.now().isoformat()
            }
            
            article_store.add_article(article)
        except Exception as e:
            print(f"Error processing article {headline['url']}: {e}")
    
    return redirect(url_for('home'))

@app.route('/clear', methods=['POST'])
def clear_articles():
    article_store.articles = []
    article_store.save_articles()
    return redirect(url_for('home'))

@app.route('/debug')
def debug_articles():
    articles = article_store.get_articles()
    
    # Get AI service status
    ai_status = {
        "g4f_client_available": USE_G4F_CLIENT,
        "g4f_legacy_available": USE_G4F_LEGACY if 'USE_G4F_LEGACY' in globals() else False,
        "last_used_model": LAST_USED_MODEL,
        "available_models": AVAILABLE_MODELS
    }
    
    debug_info = {
        'article_count': len(articles),
        'ai_status': ai_status,
        'articles': [{
            'id': a.get('id', 'No ID'),
            'title': a.get('title', 'No title'),
            'url': a.get('url', 'No URL'),
            'has_summary': a.get('has_summary', False)
        } for a in articles]
    }
    return render_template('debug.html', debug_info=debug_info)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(debug=True)
