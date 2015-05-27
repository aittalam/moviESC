# -*- coding: utf-8 -*-
#
# Scrapy-based opendir crawler for moviESC
#
# Given an opendir URL, it crawls it and saves all the URLs corresponding to movie files (avi,mp4,...)
# in a "toIndex" set on redis. The crawl is limited to URLS within the specified domain and path
#
# Run as: scrapy runspider opendirCrawler.py -s LOG_ENABLED=0 -s DOWNLOAD_DELAY=1 -a start_url="http://my.opendir.url/"
#                -a redis_host=<redis host> -a redis_port=<redis port> -a redis_db=<redis database>
#
# (if called without parameters, it will just connect to a default opendir for testing, using redis
# on localhost, port 6379, db 0)

import scrapy
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from urlparse import urlparse
import redis
import re

class OpendirCrawler(CrawlSpider):
    name = 'OpendirCrawler'

    # default parameters for redis connection, will be overwritten if they are specified on the cmdline
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
        # if a start url has been provided, set the current crawler to use it
        # (also, use its domain as allowed domain, and its path as allowed path
        # for the LinkExtractor so you never go above the provided directory)
        if kwargs.has_key('start_url'):
            self.start_urls = [kwargs.get('start_url')]
            up = urlparse(kwargs.get('start_url'))
            self.allowed_domains = [up.netloc]
            # NOTE: using up.path works only with "pure" opendirs. Websites publishing their
            #       data in an opendir-like way using software like e.g. Directory Lister
            #       (http://www.directorylister.com/) might serve directories in a different way.
            #       For instance, http://srv2.hissmedia.com/?dir=Breaking%20Bad points to a dir
            #       but the path will be recognized as a query string instead.
            #       In cases like this, up.path will appear empty, thus it will be possible
            #       for scrapy to crawl upper directories (it will still be good to get the
            #       whole website contents, btw...)
            self.rules = (
                Rule(LinkExtractor(allow=(up.path), deny_extensions=()), process_links='filter_links', follow=True),
            )
        else:
            print "[i] No start urls provided, using default one(s) (%s)" %self.start_urls

        if kwargs.has_key('redis_host'):
            self.redis_host = kwargs.get('redis_host')

        if kwargs.has_key('redis_port'):
            self.redis_port = kwargs.get('redis_port')

        if kwargs.has_key('redis_db'):
            self.redis_db = kwargs.get('redis_db')

        self.r = redis.StrictRedis(host=self.redis_host,port=self.redis_port, db=self.redis_db)
        self.r.sadd('opendirs',self.start_urls[0])

        super(OpendirCrawler, self).__init__(*args, **kwargs) 


    # As we do not actually download anything, we use filter_links only to choose which links
    # we want to follow (directories, trivially defined as links ending in "/") and which ones
    # we want to process (movie files, defined as ending in mkv|avi|mp4|m4v|ogv). Everything else
    # is thrown away
    def filter_links(self, links):
        filteredLinks = []
        ext = "(mkv|avi|mp4|m4v|ogv)"
        regex = re.compile(".*?"+ext+"$",re.I)

        for link in links:
			# if link is a directory, then follow it
            # TODO: "?dir=" is provided to properly recognize as dirs the ones which 
            #       are specified as queries (it is an in-place fix and should be removed)
            if link.url.endswith("/") or link.url.find("?dir=")>=0:
                filteredLinks.append(link)

            # if not, verify whether it is a video file: if it is then save it, otherwise skip
            else:
                res = re.match(regex,link.url)
                if res:
                    print "[i] sadd toIndex " + link.url
                    self.r.sadd('toIndex', link.url)
        return filteredLinks
