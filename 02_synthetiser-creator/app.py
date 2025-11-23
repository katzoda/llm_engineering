import os
import json
import requests
from dotenv import load_dotenv
from IPython.display import Markdown, display, update_display
from scraper import fetch_website_links, fetch_website_contents, scrape_site
from openai import OpenAI


load_dotenv(override=True)
api_key_llm = os.getenv('OPENAI_API_KEY')
api_key_search = os.getenv("GOOGLE_SEARCH_API_KEY")
search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

openai = OpenAI()
MODEL = 'gpt-5-nano'

query = "how to build simple AI agent with python"

def google_search(query, api_key, search_engine_id, num_results=10):
    """
    Perform a Google Programmable Search query
    
    query: Search query string
    api_key: Google API key
    search_engine_id: Programmable Search Engine ID (cx)
    num_results: Number of results to fetch (max 10 per API call)
    """

    base_url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "q": query,
        "key": api_key,
        "cx": search_engine_id,
        "num": num_results
    }

    response = requests.get(base_url, params=params)
    data = response.json()
    return data



# I want to construct the list of links for the user prompt
# {"results": [
# {"title": title, "link": url},
# ]}

def get_search_evaluation_links(search):
    results_for_llm = {"results": []}
    info_block = {}

    for i, link in enumerate(search['items']):
        info_block["title_" + str(i+1)] = link['title']
        info_block["link_" + str(i+1)] = link['link']
        results_for_llm["results"].append(info_block)
        info_block = {}
    return results_for_llm

def get_user_prompt():
    search_results = google_search(query, api_key_search, search_engine_id, num_results=10)
    links_for_llm = get_search_evaluation_links(search_results)
    user_prompt = f"""
    Here is the list of titles and links that resulted from the web search:
    {links_for_llm}
    Please decide which of these are the most relevant web links that could be further examined to create
    a brief study material for beginners in this topic:
    {query}.
    Please do not include youtube videos links.
    The goal is to create study material which will help beginners to start learning and help them and motivate them to continue
    studying in the first crucial weeks.
    """
    return user_prompt

link_system_prompt = """
You are provided with a list of 10 search results in a form of title and url links. The list will be provided in this format:
{
    "results": [
        {"title_1": "title", "link_1": "url"}, 
        {"title_2": "title", "link_2": "url"}
    ]
}
You are able to decide based on the title and the link which of the links would be most relevant for a research that will follow. This research is aiming
to create a brief study material for beginners.
The goal is to create study material which will help beginners to start learning and help them and motivate them to continue
studying in the first crucial weeks. 
You should respond in JSON as in this example:

{
    "links": [
        {"url": "https://full.url/goes/here/"},
        {"url": "https://another.full.url/"}
    ]
}
"""


def select_relevant_links():
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_user_prompt()}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    # json.loads turns JSON formatted text into python dictionaries
    links = json.loads(result)
    return links

