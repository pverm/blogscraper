import sys
import configparser
import xml.etree.ElementTree as ElementTree
from requests.exceptions import RequestException
from general import browser_get

config = configparser.ConfigParser()
config.read('config.ini')


def get_current_feed():
    try:
        print("Getting feed of recent blog entries")
        r = browser_get(config['DEFAULT']['feed_url'])
        return r.content.decode('utf-8')
    except RequestException as e:
        print("Could not connect to {0}\nError: {1}".format(config['DEFAULT']['feed_url'], e))
        sys.exit(1)


def parse_feed(raw_data):
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    root = ElementTree.fromstring(raw_data)
    entries = []
    for e in root.findall('atom:entry', namespace):
        url = e.find('atom:link', namespace).attrib['href']
        title = e.find('atom:title', namespace).text
        author = e.find('atom:author', namespace).find('atom:name', namespace).text
        published = e.find('atom:published', namespace).text
        entries.append((url, title, author, published))
    return entries
