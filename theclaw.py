#!/usr/bin/env python

# TheClaw - A Youtube Video Downloader

# my modules
import helper

from bs4 import BeautifulSoup

import collections
import json
import re
import schedule
import time
import urllib
import urllib2
# Python 2 -> 3 junk
# import urllib.request as urllib2
import unicodedata


# Our main class
class TheClaw:
    def __init__(self, proxy_list = None):
        self.videos = []
        self.proxy_list = proxy_list

    def log_that(self, that, verbose = True, f_name = "log.txt"):
        if verbose:
            print(that)
            
        with open(f_name, "a") as f:
            f.write(str(that) + "\n")

    def download_queue(self, f_name):
        self.load_queue(self, f_name)
        self.download_all()

    def load_queue(self, f_name):
        try:
            with open(f_name, "r") as f:
                _videos = f.read().split()

        except IOError:
            self.log_that("Could not find the queue file specified.")
            return

        self.log_that("LOADING QUEUE...")
        for v in _videos:
            self.add_video(v)

        self.log_that("QUEUE LOADED...")

    def add_video(self, video_url):
        self.videos.append(Video(video_url))
        print("video added.")

    # download all the `self.videos`
    def download_all(self, try_limit = 3):
        # print("\a")
        self.log_that("DOWNLOADS STARTED...")
        for v in self.videos:
            tries = 0
            while True:
                try:
                    if self.proxy_list:
                        v.download(proxy = self.proxy_list.pop())

                    else:
                        v.download()

                    # if download successful, break out of this while loop
                    break

                except Exception as e:
                    tries += 1
                    self.log_that("An error occured: {}".format(e))
                    self.log_that(e)
                    if tries >= try_limit:
                        self.log_that("Try limit passed... moving on to a new video.")
                        break

                    else:
                        self.log_that("Trying again with a different proxy...")


# A class for each individual video to be loaded
class Video:
    def __init__(self, url):
        self.url = url
        if self.url:
            self.html = self.load_html(self.url)
            self.title = self.get_video_title(self.html)
            self.json_data = self.parse_html_json(self.html)
            self.stream_map = self.parse_stream_map(self.json_data["args"]["url_encoded_fmt_stream_map"])
            # CHANGE [0] IF YOU WANT TO GET DIFFERENT QUALITY VIDEOS
            self.download_url = self.stream_map.get("url")[0]

    def download(self, proxy = None, https = False):
        if self.download_url:
            if proxy:
                if https:
                    _proxy = urllib2.ProxyHandler({"https": proxy})
                    
                else:
                    _proxy = urllib2.ProxyHandler({"http": proxy})
                    
                opener = urllib2.build_opener(_proxy)
                response = opener.open(self.download_url)

            else:
                response = urllib2.urlopen(self.download_url)
                
            # get the file size
            meta_data = dict(response.info().items())
            # size in bytes
            f_size = int(meta_data.get("Content-Length") or meta_data.get("content-length"))

            # CHANGE [0] IF YOU WANT TO GET DIFFERENT QUALITY VIDEOS
            f_name = "{}.{}".format(helper.slugify(self.title), self.parse_video_type(self.stream_map["type"][0]))
            # 256kb == 0.25mb
            chunk_size = 256 * 1024
            download_progress = 0

            print("DOWNLOADING: {}".format(f_name))

            with open(f_name, "wb") as f:
                while True:
                    # load a buffer
                    b = response.read(chunk_size)
                    if len(b) == 0:
                        break

                    f.write(b)

                    download_progress += len(b)
                    print("\t{}mb / {}mb".format(helper.byte_mb(download_progress), helper.byte_mb(f_size)))

    def load_html(self, video_url):
        opener = urllib2.build_opener()
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]

        response = opener.open(video_url)
        html = response.read()

        return html

    def parse_html_json(self, html):
        html = html[self.get_json_start(html):]
        html = html[:self.get_json_end(html)]
        return json.loads(html)
    
    def get_json_start(self, html):
        json_start_pattern = "ytplayer.config = "
        json_start_i = html.find(json_start_pattern)
        # move the index to the actual starting '{' of the json
        json_start_i += len(json_start_pattern)
        return json_start_i

    # WARNING: will break if the starting char is not an opening bracket
    def get_json_end(self, html):
        brackets = 0
        for i, c in enumerate(html):
            if c == "{":
                brackets += 1
            
            elif c == "}":
                brackets -= 1

            if brackets == 0:
                return i + 1

        return None

    # take the complete mess of video data and make it useful
    def parse_stream_map(self, mess):
        _map = collections.defaultdict(list)

        # the videos choices are divided by commas
        videos = mess.split(",")

        videos = [video.split("&") for video in videos]

        # split parameters into keys and values and enter into our map
        for video in videos:
            for p in video:
                try:
                    key, value = p.split("=")
                    _map[key].append(urllib.unquote(value))

                except ValueError:
                    pass

        return _map

        # extract the video title from the Youtube HTML
    def get_video_title(self, html):
        soup = BeautifulSoup(html, "html.parser")
        v_title = soup.find("title")
        v_title = str(v_title.string).split(" - YouTube")[0]
        # v_title = soup.find("span", {"id": "eow-title", "class": "watch-title"})
        # v_title = v_title.attrs["title"]

        return v_title

    # trim down all the excess video type data down to the raw extension
    def parse_video_type(self, v_type):
        v_type = v_type.split(";")[0]
        v_type = v_type.split("/")[1]
        return v_type


proxies = '''
192.241.134.241:3128
192.169.144.40:80
192.99.159.91:80
192.169.144.40:8080
192.241.186.239:8080
192.241.254.131:80
192.99.190.15:3128
192.99.190.7:80
192.241.134.241:80
192.99.190.15:80
192.99.159.91:8080
192.95.47.171:80
192.99.188.183:80
192.99.159.91:3128
192.99.190.7:8080
192.95.47.171:8080
192.241.186.239:80
192.241.254.131:8080
192.241.254.131:3128
192.99.190.7:3128
192.241.194.131:8080
192.95.21.165:80
192.99.188.183:443
'''
proxies = proxies.split()

if __name__ == "__main__":
    # Download a single video:
    # v = Video("--> Youtube video url <--")
    # v.download()

    # Schedule the download of multiple videos:
    the_claw = TheClaw(proxy_list = proxies)
    schedule.every().day.at("8:58").do(the_claw.download_queue)

    while True:
        schedule.run_pending()
        time.sleep(60)
