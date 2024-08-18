# app.py

import json
from flask import Flask, jsonify  # Correctly import Flask and jsonify
from bs4 import BeautifulSoup
import requests
from newspaper import Article
from openai import OpenAI  # Import OpenAI library
import time
from flask_cors import CORS
import logging


app = Flask(__name__)

# Apply CORS to the entire app
CORS(app)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_links(url):
    """Extracts relevant article links from the given URL."""
    try:
        response = requests.get(url)
        logging.debug("response in extract_links is ========>", response)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        anchor_tags = soup.find_all('a')
        links = [tag.get('href') for tag in anchor_tags if tag.get('href') is not None]
        substr = 'https://indianexpress.com/article'
        relevant_articles = list(set([link for link in links if substr in link]))
        logging.debug("relevant_articles ========>", relevant_articles)
        return relevant_articles
    except requests.exceptions.RequestException as e:
        logging.debug(f"Failed to retrieve the webpage. Error: {e}")
        return []

def newspaper_text_extraction(article_url):
    """Extracts text and metadata from the given article URL."""
    try:
        article = Article(article_url)
        article.download()
        article.parse()
        return article
    except Exception as e:
        logging.debug(f"Error downloading article from URL: {article_url}. Error: {e}")
        return None

def summarize_text(text, word_count):
    """Summarizes the text using OpenAI API and returns a dictionary with summary and Q&A."""
    logging.debug("Word count:", word_count)
    client = OpenAI(
        api_key="54be9686eeb04ecb8befe97e6bf30642",
        base_url="https://api.aimlapi.com",
    )

    summary = {'summary': '', 'qna': []}  
    # summary_dict = None
    if text:
        text_to_summarize = text  # Limit text to 4096 characters to fit API constraints
        try:
            # Use OpenAI's chat model for summarization and Q&A generation
            response = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",  # Replace with your desired model
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant who can summarize text."
                    },
                    {
                        "role": "user",
                        "content": f"{text_to_summarize}\n\n, after summarizing the text please create some questions along with answers. The questions should be relevant to UPSC prelims exam. You can take reference from the UPSC prelims syllabus for reference and previous year question papers for better results. Create questions only if they can be made out of the article. Create a maximum of 5 top questions from this article, The output should be a JSON with keys 'summary' for the summary text and 'qna' for questions and answers, only return the Json containing summary and qna nothing else"
                    },
                ],
            )
            time.sleep(3)  # Wait for API processing if rate-limited
            summary = response.choices[0].message.content

            if summary.startswith('```') and summary.endswith('```'):
                summary = summary[3:-3].strip()

            # print("Received summary from API:", summary)  # Debugging statement

            logging.debug("summary ===========>", summary)
        except Exception as e:
            logging.debug(f"An unexpected error occurred: {e}")
            summary = {'summary': '', 'qna': []}  # Return empty summary in case of failure
    else:
        sumamry = {'summary': '', 'qna': []}  # Handle empty text scenario
    logging.debug("Final Summary:", summary)
    return summary

def generate_response():
    """Generate the final response with article summaries and Q&A."""
    logging.debug("<===========program started from generate_response() ===========>")
    response = []
    url = 'https://indianexpress.com/todays-paper/'
    logging.debug("url is ==========>", url)
    links = extract_links(url)

    for link in links[:1]:  # Limiting to first link for demonstration
        logging.debug("Processing link:", link)
        article_url = link
        article = newspaper_text_extraction(article_url)
        if article is None:
            continue

        article_title = article.title
        article_text = article.text
        word_count = len(article_text)
        summary_dict = summarize_text(article_text, word_count)

        json_data = json.loads(summary_dict)
        logging.debug('json_data =====>', json_data)

        main_obj = {
            'title': article_title,
            'full_text': article_text,
            'summary': json_data['summary'],
            'mcq': json_data['qna']
        }

        response.append(main_obj)

    return response

@app.route('/api/articles', methods=['GET'])
def get_articles():
    logging.debug("<=========Calling /api/articles get method =========>")
    """Endpoint to get summarized articles with Q&A."""
    response_data = generate_response()
    return jsonify(response_data)

@app.route('/', methods=['GET'])
def start_message():
    logging.debug("<=========Stared with no routes==============>")
    return 'Welcome'

if __name__ == '__main__':
    logging.debug("app.py started")
    app.run(debug=True)
