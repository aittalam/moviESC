import re
import subprocess
import redis
import sys

# Relies on wget to crawl a website and applies a regex to its output to extract all
# the movie URLs (i.e. all the urls that end e.g. in avi, mkv, mp4).
# Then it saves each movie URL in a redis DB.

if len(sys.argv)<2:
	# url to crawl
	url = 'http://download.gcarena.net/movies/Gravity%20%282013%29/Gravity.mkv'
else:
	url = sys.argv[1]

# specify the extensions to catch (they are case insensitive)
ext = ext = "(mkv|avi|mp4|m4v)"
# this is the format used by wget to show the URLs it crawls
regex = re.compile('^--.*?(http.*?'+ext+')$',re.I)

# connect to redis
r = redis.StrictRedis(host='localhost',port='6379', db=0)

# save base URL for later re-crawling?
r.sadd('opendirs',url)

# run wget to crawl the website and catch all the URLs
#p = subprocess.Popen(['wget', '-A mkv,avi,mp4,m4v', '--no-check-certificate', '--spider', '--force-html', '-r', '-l0', '-np', '-nd', url], 
p = subprocess.Popen(['wget', '--no-check-certificate', '--spider', '--force-html', '-r', '-l0', '-np', '-nd', url], 
			shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# filter only the video URLs
for line in p.stdout.readlines():
	# print line,
	res = re.match(regex,line) 
	if res:
		movieURL = res.group(1)
		# currently we are not really interested in keeping an order for indexing
		# rather, it is convenient to avoid dupes, thus the idea of using a set
		r.sadd('toIndex',movieURL)
		print "[i] sadd toIndex " + movieURL

# WARNING: This will deadlock when using stdout=PIPE and/or stderr=PIPE and the child 
# process generates enough output to a pipe such that it blocks waiting for the OS 
# pipe buffer to accept more data
# ... should we just remove it? Is it going to work fine without wait()ing?
# retval = p.wait()
