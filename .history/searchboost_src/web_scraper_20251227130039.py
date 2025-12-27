import requests
from bs4 import BeautifulSoup

def scrape_results(engine, query, num_results=10):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://{engine}/search?q={query}&num={num_results}"
    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch search results from {engine}. Status code: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for result in soup.find_all('div', class_='tF2Cxc', limit=num_results):
        title = result.find('h3').text if result.find('h3') else "No title"
        link = result.find('a')['href'] if result.find('a') else "No link"
        snippet = result.find('span', class_='aCOpRe').text if result.find('span', class_='aCOpRe') else "No snippet"
        results.append({"title": title, "url": link, "snippet": snippet})

    return results

def searxng(engine, query, num_results=10):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://{engine}/search?q={query}&num={num_results}"
    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch search results from {engine}. Status code: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for result in soup.find_all('div', class_='result', limit=num_results):
        title = result.find('a', class_='result__title').text if result.find('a', class_='result__title') else "No title"
        link = result.find('a', class_='result__title')['href'] if result.find('a', class_='result__title') else "No link"
        snippet = result.find('p', class_='result__snippet').text if result.find('p', class_='result__snippet') else "No snippet"
        results.append({"title": title, "url": link, "snippet": snippet})

    return results
    
    async def test_searxng(query: str, engine: list):
        engine = "searxng.example.com"
        results = {"TEST RESUTLS FROM SEARXNG"}
        for result in results:
            print(result)