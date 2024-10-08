# app.py

import json
from flask import Flask, jsonify  # Correctly import Flask and jsonify
from bs4 import BeautifulSoup
import requests
from newspaper import Article
from openai import OpenAI  # Import OpenAI library
import time

app = Flask(__name__)

def extract_links(url):
    """Extracts relevant article links from the given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        anchor_tags = soup.find_all('a')
        links = [tag.get('href') for tag in anchor_tags if tag.get('href') is not None]
        substr = 'https://indianexpress.com/article'
        relevant_articles = list(set([link for link in links if substr in link]))
        return relevant_articles
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve the webpage. Error: {e}")
        return []

def newspaper_text_extraction(article_url):
    """Extracts text and metadata from the given article URL."""
    try:
        article = Article(article_url)
        article.download()
        article.parse()
        return article
    except Exception as e:
        print(f"Error downloading article from URL: {article_url}. Error: {e}")
        return None

def summarize_text(text, word_count):
    """Summarizes the text using OpenAI API and returns a dictionary with summary and Q&A."""
    print("Word count:", word_count)
    client = OpenAI(
        api_key="86ca7e2b44ce40d099efdddfa5a42feb",
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

            print("summary ===========>", summary)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            summary = {'summary': '', 'qna': []}  # Return empty summary in case of failure
    else:
        sumamry = {'summary': '', 'qna': []}  # Handle empty text scenario
    print("Final Summary:", summary)
    return summary

def generate_response():
    """Generate the final response with article summaries and Q&A."""
    response = []
    url = 'https://indianexpress.com/todays-paper/'
    links = extract_links(url)

    for link in links[:1]:  # Limiting to first link for demonstration
        print("Processing link:", link)
        article_url = link
        article = newspaper_text_extraction(article_url)
        if article is None:
            continue

        article_title = article.title
        article_text = article.text
        word_count = len(article_text)
        summary_dict = summarize_text(article_text, word_count)

        json_data = json.loads(summary_dict)
        print('json_data =====>', json_data)

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
    """Endpoint to get summarized articles with Q&A."""
    response_data = generate_response()
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
