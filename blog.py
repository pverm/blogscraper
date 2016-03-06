import os
import configparser
import sys
from requests.exceptions import RequestException
from datetime import datetime
from bs4 import BeautifulSoup
from general import browser_get, get_md5_hash, valid_name
from imgurpython import ImgurClient

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
        self.dirpath = os.path.join('images/{0}/[{1}] {2}'.format(author, published[:10], valid_name(title)))
        self.cookies = {}

    def __repr__(self):
        return '<Blogentry %r>' % self.url

    def download(self):
        self.get_image_urls()
        if len(self.images_awalker) > 0 or len(self.images) > 0:
            os.makedirs(self.dirpath, exist_ok=True)
            self.download_images()
            self.download_images_awalker()
        self.downloaded = True

    def download_images(self):
        for url in self.images:
            print("GET {0}".format(url))
            try:
                r = browser_get(url)
                imgpath = os.path.join(self.dirpath, get_md5_hash(r.content) + '.jpg')
                with open(imgpath, 'wb') as fout:
                    fout.write(r.content)
                print("Saved {0}".format(imgpath))
            except RequestException as e:
                print("Failed getting image from {0} ({1})".format(url, e))

    def download_images_awalker(self):
        for url in self.images_awalker:
            self.set_awalker_cookies(url)
            image_url = url.replace('img1.php?id', 'img2.php?sec_key')
            print("GET {0} (Cookies: {1})".format(image_url, self.cookies))
            try:
                r = browser_get(image_url, cookies=self.cookies)
                imgpath = os.path.join(self.dirpath, get_md5_hash(r.content) + '.jpg')
                with open(imgpath, 'wb') as fout:
                    fout.write(r.content)
                print("Saved {0}".format(imgpath))
            except RequestException as e:
                print("Failed getting image from {0} ({1})".format(url, e))

    def set_awalker_cookies(self, url):
        try:
            r = browser_get(url)
            self.cookies = r.cookies
        except RequestException as e:
            print("Failed setting cookies {0} ({1})".format(url, e))

    def get_image_urls(self):
        try:
            r = browser_get(self.url)
        except RequestException as e:
            print("Failed accessing {0} ({1})".format(self.url, e))
            return
        soup = BeautifulSoup(r.content.decode('utf-8'), 'html.parser')

        # images hosted directly on site (excluding decoration gifs)
        images = [x['src'] for x in soup.select('.entrybody img') if not x['src'].endswith('gif')]
        self.images.extend(set(images))

        # images hosted on awalker.jp
        urls = [x['href'] for x in soup.select('.entrybody div a') if 'dcimg.awalker.jp' in x['href']]
        self.images_awalker.extend(set(urls))

    def upload(self):
        self.create_album()
        for imagefile in os.listdir(self.dirpath):
            print("Uploading image '{0}' to album '{1}'".format(imagefile, self.album_id))
            fields = {'album': self.album_id}
            res = client.upload_from_path(os.path.join(self.dirpath, imagefile), config=fields, anon=False)
            print("Image '{0}' uploaded to http://imgur.com/{1}".format(imagefile, res['id']))
        self.uploaded = True

    def create_album(self):
        fields = {
            'title': self.album_title,
            'layout': 'horizontal',     # blog, grid, horizontal, vertical
            'privacy': 'public'         # public, hidden, secret
        }
        try:
            self.album_id = client.create_album(fields)['id']
        except imgurpython.helpers.error.ImgurClientRateLimitError as e:
            print('Unable to upload images: imgur API rate limit exceeded.')
            sys.exit(1)
        print("Created imgur album '{0}' at http://imgur.com/a/{1}".format(self.album_title, self.album_id))
