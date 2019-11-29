moviESC
=======

A simple, personal movie search engine, purposely built for the Powerbrowsing talk at ESC2K14 (http://www.endsummercamp.org/).

Check out the video at 
https://www.youtube.com/watch?v=j0JdX8BiuvM (unfortunately encrypted in Italian).

moviESC is a set of tools allowing you to build your own movie search engine. This includes a
crawler for movie opendirs, a movie identifier, an indexer, and few creative tools to make use of
your indexed data.

Dependencies
------------

moviESC relies on:

- Scrapy for crawling,
- Redis (>=2.8.12) as a backend,
- IMDbPY to retrieve movie metadata,
- and Flask as a rest server.


Installation
------------

- Download and install redis (see http://redis.io/ for details):

```
wget http://download.redis.io/releases/redis-5.0.7.tar.gz
tar xvfz redis-5-0-7.tar.gz
cd redis-5.0.7
make
./src/redis-server
```

- Install dependencies 

```
pip install redis Scrapy Flask IMDbPY PyYAML
```

On Debian/Raspbian systems, you might first need to satisfy some dependencies:

```
sudo apt-get install python-dev libxml2-dev libxslt-dev libffi-dev service-identity
```


First run
---------

To get acquainted with the system, cd to moviESC's directory and run the following in sequence:

```
scrapy runspider opendirCrawler.py 
```

This is the simplest way you can call the crawler, and of course it does not do much more
than crawling a default opendir (check the script to learn how to crawl any opendir). The
crawler will collect the video URLs it finds and save them in a queue (actually a set) in
Redis. To identify them, run:

```
python processURLs.py
```

(don't worry if you get some errors, not all of the videos can be identified and they were
added as a test). Finally:

```
python buildHTML.py >movies.html
```

Open movies.html... et voila'! The list of (currently one) collected movies will appear
in your browser, just click on them to download or copy the URL to VLC to stream them.

So, what use are Flask and the Chrome extension then? Well, first run the Flask server:

```
python flaskMoviESC.py 
```

Then, on Chrome, go to Menu->More Tools->Extensions, choose "Load unpacked extensions",
and open the "chrome" dir in moviESC's package. A red square will appear in your search
bar. Go to http://www.imdb.com/title/tt3268458/ and look below the movie poster :-)

(NOTE: in the current version, all the movies will show that link, even if an URL is
not available for them... will fix it ASAP)


Todos
-----

This is a very early version and, despite working well as a proof of concept (you can see it in action at the end of the talk video linked above), it is still far from being production- (probably even user-)ready. My priorities at the present time are the following:

- build a proper caching system to avoid hammering opensubtitles.org with identification requests
- make a Web front-end/API available to perform identification given a video URL
- write proper documentation and make installation + first run easier

