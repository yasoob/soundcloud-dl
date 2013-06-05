#!/usr/bin/env python
import sys
import re
import soundcloud_api
import requests
import os
import subprocess
import math
import threading
if sys.version_info[1] >= 6:  import json
else: import simplejson as json

#The string that is shown when the program loads
entrystring = \
"""A Soundcloud song searcher and downloader in python by M.Yasoob Khalid <yasoob.khld@gmail.com>"""

# setting up the headers for fooling soundcloud's servers
_useragent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.56 Safari/536.5"
htmlclient = {"User-Agent":_useragent, "Content-Type":"application/json", "Accept-Encoding":"gzip"}

# Do a search for the given query and return the results 
def song_search(song_name, result_count=20):
    """This method uses the soundcloud api to search for songs on soundcloud.
    It provides the result in a json format and you can access all the data of
    the songs. Obviously except the download url :p """

    # here we are making the tracks variable global so that we can access it outside this method
    global tracks
    client = soundcloud_api.Client(client_id='b45b1aa10f1ac2941910a7f0d10f8e28')
    try:
        tracks = client.get('/tracks', q=song_name, limit=result_count)
    except requests.exceptions.HTTPError:
        print "Check your internet connection"
        exit()

# this method converts the size given in bytes to human readable format
def convertSize(n, format='%(value).1f %(symbol)s', symbols='customary'):
    """
    Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs
    """
    SYMBOLS = {
    'customary'     : ('B', 'K', 'Mb', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'),
    'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'),
    }
    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = SYMBOLS[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)

# this method converts the time in milliseconds to human readable format.
def convertTime(ms):
    x = ms / 1000
    seconds = x % 60
    x /= 60
    minutes = x % 60
    x /= 60
    hours = x % 24
    x /= 24
    days = x
    if hours == 0:
        if minutes == 0:
            if seconds == 0:
                return "0 sec"
            else:
                return "%s sec" %str(seconds)
        else:
            return "%s min %s sec" %(str(minutes),str(seconds))
    else:
        return "%s hours %s min %s sec" %(str(hours),str(minutes),str(seconds))

# Retrieve all the information from a soundcloud url
def extract_data(url):
    """ This method takes a soundcloud song url as an input and then opens
    various urls in order to find out the actual url of the soundcloud music file."""
    global final_result
    _VALID_URL = r'^(?:https?://)?(?:www\.)?soundcloud\.com/([\w\d-]+)/([\w\d-]+)'

    # checking weather the given url is a valid soundcloud url or not
    mobj = re.match(_VALID_URL, url)
    if mobj is None:
        print u'[Soundcloud-dl]  Invalid URL: %s' %(url)
        # if the url is invalid then close the program
        sys.exit()

	# extract uploader (which is in the url)
    uploader = mobj.group(1)

    # extract simple title (uploader + slug of song title)
    slug_title =  mobj.group(2)
    simple_title = uploader + u'-' + slug_title
    full_title = '%s/%s' % (uploader, slug_title)

    # here we are just simply recreating the url
    url = 'http://soundcloud.com/%s/%s' % (uploader, slug_title)

    # here we are making the "resolve" url. 
    # We will open this url and soundcloud will give 
    # us all the information about the song except its main download url.
    resolv_url = 'http://api.soundcloud.com/resolve.json?url=' + url + '&client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
        
    print u'Resolving the given url...'
    info_json = requests.get(resolv_url, headers=htmlclient).text
    
    info = json.loads(info_json)
    video_id = info['id']

    # we are opening another url and hopefully this will be the last url
    # this url will give us the actual link to the mp3 file
    streams_url = 'https://api.sndcdn.com/i1/tracks/' + str(video_id) + '/streams?client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
    try:
       	u'[Soundcloud-dl]  Downloading stream definitions',
       	stream_json = requests.get(streams_url, headers=htmlclient).text
    except:
		u'[Soundcloud-dl]  unable to download stream definitions'
		sys.exit()

    streams = json.loads(stream_json)
    mediaURL = streams['http_mp3_128_url']
    upload_date = info['created_at']

    # and finally here are the final results in json format
    final_result = [{
        'id':       info['id'],
        'url':      mediaURL,
        'uploader': info['user']['username'],
        'upload_date': upload_date,
        'title':    info['title'],
        'ext':      u'mp3',
        'description': info['description'],
    }]	

# this tells us weather the script was directly run or not.
# If it is directly run then the code bellow this comment executes.
if __name__ == '__main__':
    print entrystring

    # we are asking the user which song does he want to download.
    song = raw_input("[Soundcloud-dl]  Which song do you want?\t")
    print "Searching for '%s'..."%(song)
    
    # here we are running the search method using the given query
    song_search(song)
    
    #default dictionary for holding the results
    result = {}

    # a variable simply to keep track of the songs
    # this variable will allows us to retrieve back the song which the user demands.
    count = 1

    # simply looping over the tracks variable produced by song_search method and assigning it to a dictionary
    for i in tracks:    
        #another dictionary for holding all the results for a specific song
        result[count] = {}
        result[count]['title'] = i.title
        result[count]['uploader'] = i.user['username']
        result[count]['duration'] = convertTime(i.duration)
        result[count]['size'] = convertSize(i.original_content_size)
        result[count]['url'] = i.permalink_url 

        # here we are incrementing the count variable by 1 everytime the loop runs
        count += 1

    # here we are looping over the dictionary 
    for k,i in enumerate(result):
        # and printing the results on screen
        print str(k+1) + ": "+result[i]['title']+" --by-- " +result[i]['uploader']

    # here we are asking the user which song he wants to download
    user_choice = raw_input('\nEnter the Song ID you wish to download or (q) to exit: ')

    #Exit if choice is empty or q
    if user_choice == "" or user_choice == "q": exit() 

    # here we are running the extract_data method according to the user_choice variable
    extract_data(result[int(user_choice)]['url'])
    
    # looping over the final results received after resolving the url
    for i in final_result: 
        cmd = 'wget -O "%s.mp3" "%s" "--no-check-certificate"' % (i['title'],i['url']) #Run wget to download the song
        p = subprocess.Popen(cmd, shell=True)
        try:
            p.wait() #Wait for wget to finish
        except KeyboardInterrupt: #If we are interrupted by the user
            os.remove('%s.mp3' %(i['title'])) #Delete the song
            print "\nDownload cancelled. File deleted."
    # Natural exit