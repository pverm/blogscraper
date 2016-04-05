import sys
import configparser
import logging
import xml.etree.ElementTree as ElementTree
from requests.exceptions import RequestException
from general import browser_get


def get_feed(url):
    try:
        logging.info("Getting feed {}".format(url))
        r = browser_get(url)
        return r.content.decode('utf-8')
    except RequestException as e:
        logging.error("Could not connect to {0}: {1}".format(url, e))
        sys.exit(1)


def parse_feed(raw_data):
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    root = ElementTree.fromstring(raw_data)
    entries = []
    for e in root.findall('atom:entry', namespace):
        url = e.find('atom:link', namespace).attrib['href']
        title = e.find('atom:title', namespace).text or 'Untitled'
        author = e.find('atom:author', namespace).find('atom:name', namespace).text
        published = e.find('atom:published', namespace).text
        entries.append((url, title, author, published))
    return entries
