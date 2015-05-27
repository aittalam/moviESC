moviESC
=======

A simple, personal movie search engine, purposely built for the Powerbrowsing talk at ESC2K14 (http://www.endsummercamp.org/).

Check out the talk slides at https://www.dropbox.com/s/w4f24yrq13n15im/pb_ESC.pdf and the video at
https://www.youtube.com/watch?v=j0JdX8BiuvM (unfortunately, both are encrypted in Italian).

moviESC is a set of tools allowing you to build your own movie search engine. This includes a
crawler for movie opendirs, a movie identifier, an indexer, and few creative tools to make use of
your indexed data.

Dependencies
------------

moviESC relies on:

- Scrapy for crawling,
- Redis (>=2.8.12) as a backend,
- Flask as a rest server.

Installation
------------

- Download and install redis (see http://redis.io/)

```
pip install scrapy
pip install redis
pip install flask
```


Todo
----

This is a very early version and, despite working well as a proof of concept (you can see it in action at the end of the talk video linked above), it is still far from being production- (probably even user-)ready. My priorities at the present time are the following:

- build a proper caching system to avoid hammering opensubtitles.org with identification requests, and bootstrapping the system with some collected URLs
- make a Web front-end/API available to perform identification given a video URL
- write proper documentation and make installation + first run easier

