from urllib.request import urlopen
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['web_crawler']
pages_collection = db['pages']

class Frontier():
    def __init__(self, initial_url):
        self.frontier = [initial_url]
        self.visited = set()

    def done(self):
        return len(self.frontier) == 0

    def nextURL(self):
        return self.frontier.pop(0)

    def addURL(self, url):
        if url not in self.visited and url not in self.frontier:
            self.frontier.append(url)

    def markVisited(self, url):
        self.visited.add(url)

    def clearFrontier(self):
        self.frontier = []


def retrieveHTML(url):
    try:
        response = urlopen(url)
        return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error retrieving {url}: {e}")
        return None

def storePage(url, html):
    page = {
        'url': url,
        'html': html
    }
    pages_collection.insert_one(page)

def target_page_found(html):
    soup = BeautifulSoup(html, 'html.parser')
    target_heading = soup.find('h1', class_='cpp-h1',string=re.compile(r'Permanent Faculty'))
    return target_heading is not None


def parseHTML(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        
        if parsed_url.path.endswith(('.html', '.shtml')):
            links.add(full_url)

    return links

def crawlerThread():
    frontier = Frontier("https://www.cpp.edu/sci/computer-science/")
    target_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"

    while not frontier.done():
        url = frontier.nextURL()
        html = retrieveHTML(url)
        storePage(url, html) 
        if target_page_found(html):
            print(f"Found the URL {url}")
            frontier.clearFrontier() 
        else:
            if url == target_url:
                print('Error: Found target but did not recognize')
                break
            print(url)
            frontier.markVisited(url)
            links = parseHTML(html, url)
            for link in links:
                frontier.addURL(link)

if __name__ == "__main__":
    crawlerThread()