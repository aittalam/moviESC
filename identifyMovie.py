import init
import urllib, urllib2
import struct
import sys
import re
from trivialScraper import getAndExtract

# load configuration params and start logger
conf,logger = init.configure()
if conf is None:
    logger.error("Could not open config file, reverting to defaults")

URL_OS = 'http://www.opensubtitles.org/en/search/sublanguageid-all/moviebytesize-BYTESIZE/moviehash-HASH'
RE_IMDBID = 'imdb.com/title/tt(\d+)/'

def hashURL(url):
    try:
        longlongformat = 'q'  # long long 
        bytesize = struct.calcsize(longlongformat)
   
        # get file size
        headers = urllib2.urlopen(url).info().getheaders("Content-Length")
        if len(headers) == 0 : 
            logger.error('No Content-Length header available')
            return None,None
        filesize  = headers[0]
        hash = long(filesize)
        
        # work on first 64KB of the file
        r = urllib2.Request(url)
        r.headers['Range'] = 'bytes=%s-%s' % (0, 65535)
        f = urllib2.urlopen(r)
        for x in range(65536/bytesize):
            buffer = f.read(bytesize)
            (l_value,)= struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number  
    
        # work on last 64KB of the file
        r.headers['Range'] = 'bytes=%s-' % (long(filesize)-65536)
        f = urllib2.urlopen(r)
        for x in range(65536/bytesize):
            buffer = f.read(bytesize)
            (l_value,)= struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF
    
        returnedhash = "%016x" % hash
        return filesize,returnedhash

    except urllib2.HTTPError, e:
        logger.error('HTTPError: %s.' % e.code)
        return None,None
    
    except urllib2.URLError, e:
        logger.error('URLError: %s.' % e.reason)
        return None,None
    
    except:
        logger.error("hashURL failed with an unexpected error")
        return None,None


# gets IMDB id from opensubtitles 
def getIMDBid(bytesize,movhash):
        # first check if the IMDBid is cached

        # if not, first get it from opensubtitles
        url = URL_OS.replace("BYTESIZE",str(bytesize)).replace("HASH",movhash)
        # get the IMDB ID from opensubtitles
        m = getAndExtract(url, RE_IMDBID)
        if not m :
                logger.error('Could not get IMDB ID from opensubtitles.org (check %s)' % url)
                return
        return m.group(1)


if __name__ == '__main__':

    if len(sys.argv)<2:
        url = 'https://archive.org/download/TheInternetsOwnBoyTheStoryOfAaronSwartz/TheInternetsOwnBoy_TheStoryofAaronSwartz-HD.mp4'
    else: 
        url = sys.argv[1]
	

    logger.info("Hashing %s..." % url)
    s,h = hashURL(url)
    logger.info('Size: %s, Hash: %s' % (str(s), str(h)))

    if not s or not h:
        logger.error("Could not determine size or hash: exiting")
        exit()

    logger.info("Identifying movie... ")
    IMDBid = getIMDBid(s,h)
    if not IMDBid:
        logger.error("[x] Could not determine IMDB id")
    else:
	    logger.info('==> http://www.imdb.com/title/tt' + IMDBid)
