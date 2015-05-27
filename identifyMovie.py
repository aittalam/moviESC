import urllib, urllib2
import struct
import sys
import re

URL_OS = 'http://www.opensubtitles.org/en/search/sublanguageid-all/moviebytesize-BYTESIZE/moviehash-HASH'
URL_MP_MOVIE = 'http://www.movieposterdb.com/movie/'
URL_MP_POSTER = 'http://www.movieposterdb.com/poster/'

RE_IMDBID = 'imdb.com/title/tt(\d+)/'
RE_MP_POSTER = 'id="poster_([^"]+)"[^>]+width: 310'
RE_MP_IMG = 'property="og:image" content="([^"]+)"'

def getAndExtract(url, regex):
	try:
        	response = urllib2.urlopen(url)
        	content = response.read()
        	m = re.search(regex,content)
        	return m

	except urllib2.HTTPError, e:
		print '[x] We failed with error code %s.' % e.code
		return
	
	except urllib2.URLError, e:
		print '[x] We failed with an URLError: %s' % e.reason
		return

def getPosterURL(IMDBid):
        # get a poster page (the bigger/main one) from movieposterdb
        m = getAndExtract(URL_MP_MOVIE + str(IMDBid), RE_MP_POSTER)
        if not m :
                print '[x] Could not get poster page from movieposterdb'
                return
        # get the actual poster image URL from the poster page
        m = getAndExtract(URL_MP_POSTER + str(m.group(1)), RE_MP_IMG)
        if not m :
                print '[x] Could not get poster URL from movieposterdb'
                return
        # return the URL
        return m.group(1)


def getURLSize(url):
	try:
		headers = urllib2.urlopen(url).info().getheaders("Content-Length")
		if len(headers) > 0 : 
			return headers[0]
		else:
			print '[x] No Content-Length header available'

	except urllib2.HTTPError, e:
		print '[x] We failed with error code %s.' % e.code
		return

	except urllib2.URLError, e:
		print '[x] We failed with an URLError: %s' % e.reason
		return

def hashURL(url):
	try:
		longlongformat = 'q'  # long long 
		bytesize = struct.calcsize(longlongformat)

		r = urllib2.Request(url)
		
		filesize  = getURLSize(url)
		if not filesize:
			print '[x] Could not get movie size'
			return None,None
		hash = long(filesize)

		r.headers['Range'] = 'bytes=%s-%s' % (0, 65535)
		f = urllib2.urlopen(r)
                for x in range(65536/bytesize):
                        buffer = f.read(bytesize)
                        (l_value,)= struct.unpack(longlongformat, buffer)
                        hash += l_value
                        hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number  

		r.headers['Range'] = 'bytes=%s-' % (long(filesize)-65536)
		f = urllib2.urlopen(r)
		for x in range(65536/bytesize):
                        buffer = f.read(bytesize)
                        (l_value,)= struct.unpack(longlongformat, buffer)
                        hash += l_value
                        hash = hash & 0xFFFFFFFFFFFFFFFF

                returnedhash =  "%016x" % hash
                return filesize,returnedhash
	
	except urllib2.HTTPError, e:
		print '[x] We failed with error code %s.' % e.code
		return None,None

	except urllib2.URLError, e:
		print '[x] We failed with an URLError: %s' % e.reason
		return None,None

	except Exception, e:
		print e.__doc__
		print e.message
		return None,None
	else:
		print '[x] hashURL failed with some unknown error'
		return None,None


# gets IMDB id from opensubtitles 
# TODO: plan a simple title search in IMDB if automatic identification fails
def getIMDBid(bytesize,movhash):
        url = URL_OS.replace("BYTESIZE",str(bytesize)).replace("HASH",movhash)
        # get the IMDB ID from opensubtitles
        m = getAndExtract(url, RE_IMDBID)
        if not m :
                print '[x] Could not get IMDB ID from opensubtitles.org'
                print '    Check ' + url
                return
        return m.group(1)


if __name__ == '__main__':

    if len(sys.argv)<2:
        url = 'https://archive.org/download/TheInternetsOwnBoyTheStoryOfAaronSwartz/TheInternetsOwnBoy_TheStoryofAaronSwartz-HD.mp4'
    else: 
        url = sys.argv[1]
	

    print "Hashing %s..." % url
    s,h = hashURL(url)
    print 'Size: %s, Hash: %s' % (str(s), str(h))

    if not s or not h:
        print "Could not determine size or hash: exiting"
        exit()

    print "Identifying movie... "
    IMDBid = getIMDBid(s,h)
    if not IMDBid:
        print "Could not determine IMDB id"
    else:
	    print 'http://www.imdb.com/title/tt' + IMDBid
