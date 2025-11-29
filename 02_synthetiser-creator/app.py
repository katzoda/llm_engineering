import os
import json
import requests
import asyncio
from dotenv import load_dotenv
from IPython.display import Markdown, display, update_display
from scraper import scrape_multiple_sites
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from openai import OpenAI


load_dotenv(override=True)
api_key_llm = os.getenv('OPENAI_API_KEY')
api_key_search = os.getenv("GOOGLE_SEARCH_API_KEY")
search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

openai = OpenAI()
MODEL = 'gpt-5-nano'



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

query = "how to build simple AI agent with python"
search_results = {}
search_results = google_search(
    query=query,
    api_key=api_key_search,
    search_engine_id=search_engine_id
    )


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

relevant_links = select_relevant_links()

urls = []
for link in relevant_links['links']:
    print(link['url'])
    urls.append(link['url'])

scrape_results = asyncio.run(scrape_multiple_sites(urls))


def text_parser(results):
    web_contents = {"contents": []}
    link_content = {}
    for result in results:
        soup = BeautifulSoup(result[2], 'html.parser')
        for element in soup(["script", "style", "img", "input"]):
            element.decompose()
        text = soup.get_text(separator="\n", strip=True)
        link_content["url"] = result[0]
        link_content["title"] = result[1]
        link_content["content"] = text[:2000]
        web_contents["contents"].append(link_content)
        link_content = {}
    return web_contents

text_parser(scrape_results)["contents"][0]


# create new system prompt for the guide creation

guide_system_prompt = """
You are provided with a list of relevant search results in a form of url, title and content of the website.
The list will be provided in this format:

{
    "contents": [
        {"url": "https://full.url/here/", "title": "webpage title", "content": "content of the website"}, 
        {"url": "https://another.full.url/here/", "title": "webpage title", "content": "content of the website"}
    ]
}
You are able to create a brief study material for beginners for the topic you will be provided.

Please create a brief study material which will help beginners to start learning the topic. It is not a comprehensive material but
it should help students at the start of their journey and motivate them to continue and stay ont the track during the first days.
Please also give students useful tips how to stay motivated. 

"""


# create user prompt for the guide creation

# present a query as a JSON to an LLM
query = {"topic": query}

def get_guide_prompt(resources):
    guide_user_prompt = f"""
    You are experienced tutor and creator of the various studying and teaching materials.

    Please create a brief study material which will help beginners to start learning the following topic:
    {query} 
    It is not a comprehensive material but it should help students at the start of their journey and motivate them to continue 
    and stay ont the track during the first days. Please also give students useful tips how to stay motivated.

    Here are the relevant resources you have available for the task:
    {text_parser(resources)} 
    """
    return guide_user_prompt


def get_guide():
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": guide_system_prompt},
            {"role": "user", "content": get_guide_prompt(scrape_results)}
        ]
    )
    result = response.choices[0].message.content
    return result


guide = get_guide()

display(Markdown(guide))



