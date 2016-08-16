import os
import configparser
import logging
import subprocess
from requests.exceptions import RequestException
from datetime import datetime
from bs4 import BeautifulSoup
from general import browser_get, get_md5_hash, valid_name
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientRateLimitError

config = configparser.ConfigParser()
config.read('config.ini')

client = ImgurClient(config['imgur']['client_id'],
                     config['imgur']['client_secret'],
                     refresh_token=config['imgur']['refresh_token'])


class Blogentry:

    def __init__(self, url, title, author, published, downloaded=False, uploaded=False):
        self.url = url
        self.title = title
        self.author = author
        self.published = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ')
        self.downloaded = downloaded
        self.uploaded = uploaded
        self.images_awalker = []
        self.images = []
        self.album_id = ''
        self.album_title = ('[{0}] {1} - {2}'.format(published[:10], author, title))
        self.dirpath = os.path.join(config['DEFAULT']['download_dir'], author,
                                    '[{0}] {1}'.format(published[:10], valid_name(title)))
        self.cookies = {}

    def __repr__(self):
        return '<Blogentry %r>' % self.url

    def download(self):
        self.get_image_urls()
        if len(self.images_awalker) > 0 or len(self.images) > 0:
            os.makedirs(self.dirpath, exist_ok=True)
            self.download_images()
            self.download_images_awalker()
            self.save_screenshot()
        self.downloaded = True

    def download_images(self):
        for url in self.images:
            logging.info("GET {0}".format(url))
            try:
                r = browser_get(url)
                imgpath = os.path.join(self.dirpath, get_md5_hash(r.content) + '.jpg')
                with open(imgpath, 'wb') as fout:
                    fout.write(r.content)
                logging.info("Saved {0}".format(imgpath))
            except RequestException as e:
                logging.error("Failed getting image from {0} ({1})".format(url, e))

    def download_images_awalker(self):
        for url in self.images_awalker:
            self.set_awalker_cookies(url)
            image_url = url.replace('img1.php?id', 'img2.php?sec_key')
            logging.info("GET {0} (Cookies: {1})".format(image_url, self.cookies))
            try:
                r = browser_get(image_url, cookies=self.cookies)
                imgpath = os.path.join(self.dirpath, get_md5_hash(r.content) + '.jpg')
                with open(imgpath, 'wb') as fout:
                    fout.write(r.content)
                logging.info("Saved {0}".format(imgpath))
            except RequestException as e:
                logging.error("Failed getting image from {0} ({1})".format(url, e))

    def set_awalker_cookies(self, url):
        try:
            r = browser_get(url)
            self.cookies = r.cookies
        except RequestException as e:
            logging.error("Failed setting cookies {0} ({1})".format(url, e))

    def get_image_urls(self):
        try:
            r = browser_get(self.url)
        except RequestException as e:
            logging.error("Failed accessing {0} ({1})".format(self.url, e))
            return
        soup = BeautifulSoup(r.content.decode('utf-8'), 'html.parser')

        # images hosted directly on site (excluding decoration gifs)
        images = [x['src'] for x in soup.select('.entrybody img') if not x['src'].endswith('gif')]
        self.images.extend(set(images))

        # images hosted on awalker.jp
        urls = [x['href'] for x in soup.select('.entrybody div a') if 'dcimg.awalker.jp' in x['href']]
        self.images_awalker.extend(set(urls))
        
    def save_screenshot(self):
        try:
            returncode = subprocess(["node", "-v"])
        except FileNotFoundError:
            logging.error("Node not installed! Can't run get_screen.js script")
            return
        filepath = os.path.join(self.dirpath, 'screenshot.png')
        screenshot = open(filepath, 'wb')
        returncode = subprocess.call(['node', 'get_screen.js', self.smph(self.url)], stdout=screenshot)
        screenshot.close()
        # without stream
        # subprocess.call(["node", "get_screen.js", self.url, self.filepath])
        if returncode == 0:
            logging.info("Saved screenshot of {}".format(self.url))
        elif returncode == 2:
            logging.error("Node module 'webshot' not installed! Can't run get_screen.js script")
        else:
            logging.error("Couldn't save screenshot of {}".format(self.url))
            
    def smph(self):
        # get mobile version of site
        spliturl = self.url.split('/')
        spliturl.insert(4, 'smph')
        return '/'.join(spliturl)

    def upload(self):
        self.create_album()
        for imagefile in os.listdir(self.dirpath):
            logging.info("Uploading image '{0}' to album '{1}'".format(imagefile, self.album_id))
            fields = {'album': self.album_id}
            res = client.upload_from_path(os.path.join(self.dirpath, imagefile), config=fields, anon=False)
            logging.info("Image '{0}' uploaded to http://imgur.com/{1}".format(imagefile, res['id']))
        self.uploaded = True

    def create_album(self):
        fields = {
            'title': self.album_title,
            'layout': 'horizontal',     # blog, grid, horizontal, vertical
            'privacy': 'public'         # public, hidden, secret
        }
        try:
            self.album_id = client.create_album(fields)['id']
        except ImgurClientRateLimitError as e:
            logging.error('Unable to upload images: imgur API rate limit exceeded.')
            os._exit(1)
        logging.info("Created imgur album '{0}' at http://imgur.com/a/{1}".format(self.album_title, self.album_id))
