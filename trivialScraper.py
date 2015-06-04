import init
import urllib, urllib2
import re

# load configuration params and start logger
conf,logger = init.configure()
if conf is None:
    logger.error("Could not open config file, reverting to defaults")

# trivial code to get a page and extract a single string with a regexp 
# (currently used for IMDBid from opensubtitles and movie poster from movieposterdb)
# returns None if an error occurs
# returns a regular expression match otherwise
def getAndExtract(url, regex):
    try:
        response = urllib2.urlopen(url)
        content = response.read()
        m = re.search(regex,content)
        return m

    except urllib2.HTTPError, e:
        logger.error('HTTPError: %s.' % e.code)
        return

    except urllib2.URLError, e:
        logger.error('URLError: %s.' % e.reason)
        return

