import logging
import configparser
import sys
from general import load_blog_entries, save_blog_entries, older_than_14_days
from feed import get_current_feed, parse_feed
from blog import Blogentry
from queue import Queue
from threading import Thread


def worker():
    while True:
        item = queue.get()
        logging.info("Crawling {0}".format(item.url))
        item.download()
        # item.upload()
        entry_dict[item.url] = item.url
        save_blog_entries(entry_dict)
        logging.info("Done with {0} | {1} items left in queue".format(item.url, queue.qsize()))
        queue.task_done()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    logging.basicConfig(filename=config['DEFAULT']['log_file'],
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)

    entry_dict = load_blog_entries()
    logging.info("Loaded %s blog entries from disk" % len(entry_dict))
    queue = Queue()
    for url, title, author, published in reversed(parse_feed(get_current_feed())):
        if url in entry_dict:
            continue
        if older_than_14_days(published):
            continue
        else:
            queue.put(Blogentry(url, title, author, published))
            logging.info("Added new blog entry to queue: {0} | {1} items in queue".format(url, queue.qsize()))

    t = Thread(target=worker)
    t.daemon = True
    t.start()
    queue.join()
    logging.info("Queue empty. Exiting")


