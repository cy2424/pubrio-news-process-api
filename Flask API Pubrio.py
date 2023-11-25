from flask import Flask, request, jsonify
import requests
import openai
import os

app = Flask(__name__)

# Miniflux API details
MINIFLUX_API_ENDPOINT = "https://feeds.pubrio.com/v1/"
MINIFLUX_API_KEY = "NF_IFGcUPpGD5OdkKYgmcN1070445n8NC7TKe9jEyRw="

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_content(content, summary_length=1000):
    """
    Summarize the content to a specified length using OpenAI's summarization capabilities.

    Parameters:
    - content: The original content to summarize.
    - summary_length: The maximum number of tokens for the summary.

    Returns:
    - A summary of the original content.
    """
    # Summarization prompt
    summarize_prompt = f"Please summarize the following content into a concise summary of no more than {summary_length} tokens:\n\n{content}"

    # Call the OpenAI API to summarize the content
    summary_response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=summarize_prompt,
        max_tokens=summary_length,
        n=1,
        stop=None,
        temperature=0.3,
    )

    # Extract the summarized content
    summarized_content = summary_response.choices[0].text.strip()
    return summarized_content

def extract_information(content):
    """
    Function to send a prompt to the OpenAI API and extract the required information.
    """
    # First, summarize the content to reduce its length due to limited tokens
    summarized_content = summarize_content(content)

    prompt = f"""
    Given the following article content, identify any mentioned companies and their domains, and summarize the main topic of the article. Then, present the information in a JSON format with two keys: "related_companies", which is an array of objects containing "company_name" and "company_domain", and "topic", which is a string describing the main topic or announcement of the article.

    Article content:
    {summarized_content}

    Please structure the information as follows:
    {{
      "related_companies": [
        {{
          "company_name": "Name of the first company",
          "company_domain": "Domain of the first company"
        }},
        {{
          "company_name": "Name of the second company",
          "company_domain": "Domain of the second company"
        }}
      ],
      "topic": "The main topic or announcement of the article"
    }}
    """

    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=prompt,
      max_tokens=150,
      n=1,
      stop=None,
      temperature=0.5,
    )
    
    return response.choices[0].text.strip()


def fetch_rss_feed_from_miniflux(feed_id):
    headers = {"Authorization": f"Token {MINIFLUX_API_KEY}"}
    response = requests.get(f"{MINIFLUX_API_ENDPOINT}feeds/{feed_id}/entries", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

@app.route('/analyze-rss-feed', methods=['POST'])
def analyze_rss_feed():
    data = request.json
    feed_id = data['feed_id']
    
    feed_data = fetch_rss_feed_from_miniflux(feed_id)

    if not feed_data:
        return jsonify({"error": "Failed to fetch feed data"}), 500

    analysis_results = []
    for entry in feed_data['entries']:
        content = entry.get('content', entry.get('summary', ''))
        if content:
            analysis = extract_information(content)
            analysis_results.append(analysis)

    return jsonify(analysis_results)

if __name__ == '__main__':
    app.run(debug=True)
