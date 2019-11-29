# -*- coding: utf-8 -*-
#
# Scrapy-based opendir crawler for moviESC
#
# Given an opendir URL, it crawls it and saves all the URLs corresponding to movie files (avi,mp4,...)
# in a "toIndex" set on redis. The crawl is limited to URLS within the specified domain and path
#
# Run as: scrapy runspider opendirCrawler.py -s LOG_ENABLED=0 -s DOWNLOAD_DELAY=1 -a start_url="http://my.opendir.url/"
#  (optional)    -a redis_host=<redis host> -a redis_port=<redis port> -a redis_db=<redis database>
#  (optional)    -a config_file=<configuration file> (see config.yaml)
#
# (if called without parameters, it will just connect to a default opendir for testing, using redis
# on localhost, port 6379, db 0)

import init
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urlparse
import redis
import re
import url

# trivial way to check whether a URL points to a video file
def isVideoURL(url):
    ext = "(mkv|avi|mp4|m4v|ogv)"
    regex = re.compile(".*?"+ext+"$",re.I)
    return re.match(regex,url) is not None


class OpendirCrawler(CrawlSpider):
    name = 'OpendirCrawler'

    # default parameters for redis connection, will be overwritten if they are
    # specified on the cmdline or provided in the configuration
    redis_host = 'localhost'
    redis_port = '6379'
    redis_db = '0'

    # set default start url, allowed domain, and rule
    # (they will be used if no url is passed via the -a start_url="..." parameter on the command line
    start_urls = ['http://davide.eynard.it/zelif/zeivom/']
    allowed_domains = ['davide.eynard.it']

    rules = (
        Rule(LinkExtractor(allow=('/zelif/zeivom/'), deny_extensions=()), process_links='filter_links', follow=True),
    )


    def __init__(self, *args, **kwargs):


        # load configuration params and start logger
        cfgFileName = 'config.yaml'
        if 'config_file' in kwargs:
            cfgFileName = kwargs.get('config_file')

        self._conf,self._logger = init.configure(config=cfgFileName)

        if self._conf is not None:
            self.redis_host = self._conf['redis_host']
            self.redis_port = self._conf['redis_port']
            self.redis_db = self._conf['redis_db']
        else:
            # self.logger becomes the default logger
            self._logger.error("Could not open config file, reverting to defaults")

        # if different host/port/db are passed, override config file
        if 'redis_host' in kwargs:
            self.redis_host = kwargs.get('redis_host')

        if 'redis_port' in kwargs:
            self.redis_port = kwargs.get('redis_port')

        if 'redis_db' in kwargs:
            self.redis_db = kwargs.get('redis_db')

        # if a start url has been provided, set the current crawler to use it
        # (also, use its domain as allowed domain, and its path as allowed path
        # for the LinkExtractor so you never go above the provided directory)
        if 'start_url' in kwargs:
            self.start_urls = [kwargs.get('start_url')]
            up = urlparse(kwargs.get('start_url'))
            self.allowed_domains = [up.netloc]
            # NOTE: using up.path works only with "pure" opendirs. Websites publishing their
            #       data in an opendir-like way using software like e.g. Directory Lister
            #       (http://www.directorylister.com/) might serve directories in a different way.
            #       In cases like this, up.path will appear empty, thus it will be possible
            #       for scrapy to crawl upper directories (it will still be good to get the
            #       whole website contents, btw...)
            self.rules = (
                Rule(LinkExtractor(allow=(up.path), deny_extensions=()), process_links='filter_links', follow=True),
            )
        else:
            self._logger.info("No start urls provided, using default one(s) (%s)" %self.start_urls)

        self._logger.info("Storing URLs in Redis (%s:%s, db %s)" %(self.redis_host,self.redis_port,self.redis_db))
        self.r = redis.StrictRedis(host=self.redis_host,port=self.redis_port, db=self.redis_db)
        self.r.sadd(self._conf['key_opendirs'],self.start_urls[0])

        super(OpendirCrawler, self).__init__(*args, **kwargs)

    # As we do not actually download anything, we use filter_links only to choose which links
    # we want to follow (directories, trivially defined as links ending in "/") and which ones
    # we want to process (movie files, defined as ending in mkv|avi|mp4|m4v|ogv). Everything else
    # is thrown away
    def filter_links(self, links):
        filteredLinks = []
        print(links)

        for link in links:
			      # if link is a directory, then follow it
            # TODO: "?dir=" is provided to properly recognize as dirs the ones which
            #       are specified as queries (it is an in-place fix and should be removed)
            if link.url.endswith("/") or link.url.find("?dir=")>=0:
                filteredLinks.append(link)

            # if not, verify whether it is a video file: if it is then save it, otherwise skip
            else:
                if isVideoURL(link.url):
                    # normalize the URL
                    normLinkURL = link.url
                    #normLinkURL = url.parse(link.url).canonical().escape().punycode().utf8()
                    

                    # save the url... but only if it has not been indexed yet
                    # check if the URL exists in redis
                    if not self.r.exists(normLinkURL):
                        # if not, add it to the toIndex queue
                        # (NOTE: it might be already present in toIndex, but we don't mind as it is a set)
                        self._logger.info("sadd %s %s " % (self._conf['key_toIndex'],normLinkURL))
                        self.r.sadd(self._conf['key_toIndex'], normLinkURL)
        return filteredLinks
