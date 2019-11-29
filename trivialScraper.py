import init
import urllib.request as ur
import urllib.error as ue
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
        response = ur.urlopen(url)
        content = str(response.read())
        m = re.search(regex,content)
        return m

    except ue.HTTPError as e:
        logger.error('HTTPError: %s.' % e.code)
        return

    except ue.URLError as e:
        logger.error('URLError: %s.' % e.reason)
        return

