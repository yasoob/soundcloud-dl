#!/usr/bin/env python
import sys
import re
import soundcloud
import requests
if sys.version_info[1] >= 6:  import json
else: import simplejson as json

#The string that is shown when the program loads
entrystring = \
"""A Soundcloud song searcher and downloader in python by M.Yasoob Khalid <yasoob.khld@gmail.com>"""

# setting up the headers for fooling soundcloud's servers
_useragent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.56 Safari/536.5"
htmlclient = {"User-Agent":_useragent, "Content-Type":"application/json", "Accept-Encoding":"gzip"}

def single_url(url):
    """ This method is same as extract_data() (located further down the page) method but in this method we are opening two urls to obtain
    all the required information about a soundcloud url. It takes only a soundcloud song url as an input and then opens
    various urls in order to find out the actual url of the soundcloud music file."""
    
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
        
    print u'[Soundcloud-dl]  Resolving the given url...'
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
    return {
        'id':       info['id'],
        'url':      mediaURL,
        'uploader': info['user']['username'],
        'upload_date': upload_date,
        'title':    info['title'],
        'ext':      u'mp3',
        'description': info['description'],
    }

# Do a search for the songs of a specific user and return the results
def user_song_search(user_name):
    """This method uses the soundcloud api to search for songs uploaded by a specific
    user on soundcloud. It provides the result in a json format and you can access all the data of
    the songs."""

    global tracks
    client = soundcloud.Client(client_id='b45b1aa10f1ac2941910a7f0d10f8e28')

    # here we are first resolving the artist's url and retrieving its id from soundcloud
    user_name = 'http://soundcloud.com/%s' %(user_name)
    id_search = client.get('/resolve', url=user_name) 
    userid = id_search.id
    
    try:
        tracks = client.get('/users/%s/tracks'% (userid))
    except requests.exceptions.HTTPError:
        print "Check your internet connection"
        exit()


# Do a search for the given query and return the results 
def song_search(song_name, result_count=20):
    """This method uses the soundcloud api to search for songs on soundcloud.
    It provides the result in a json format and you can access all the data of
    the songs. Obviously except the download url :p """

    # here we are making the tracks variable global so that we can access it outside this method
    global tracks
    client = soundcloud.Client(client_id='b45b1aa10f1ac2941910a7f0d10f8e28')
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

# this is our downloader
def downloader(url,filename):
    import urllib2
    ## DEFINE THE FULL URL OF FILE YOU WANT TO GRAB HERE 
    fileurl = url
     
    ## File name carving
    file_name = filename
     
    ##Initiate download
    u = urllib2.urlopen(fileurl)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "[Soundcloud-dl]  Downloading %s (%s bytes)" %(file_name, file_size)
     
    #Calculate downloaded filesize
    file_size_dl = 0
    block_size = 8192
     
    #Download loop
    while True:
        buffer = u.read(block_size)
        if not buffer:
            break
     
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%s [%3.2f%%]" % (convertSize(file_size_dl), file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        #print status
        sys.stdout.write("\r        %s" % status)
        sys.stdout.flush()
     
    #Download done. Close file stream
    f.close()

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
def extract_data(url,video_id,title):
    """ This method takes a soundcloud song url and some other info about the song as an input and then opens
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
    
    # and finally here are the final results in json format
    final_result = [{
        'url':      mediaURL,
        'title':    title,
    }]	

def for_song():
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
        result[count]['id'] = i.id
        result[count]['title'] = i.title
        result[count]['uploader'] = i.user['username']
        result[count]['duration'] = convertTime(i.duration)
        result[count]['size'] = convertSize(i.original_content_size)
        result[count]['url'] = i.permalink_url 

        # here we are incrementing the count variable by 1 everytime the loop runs
        count += 1

    # this variable contains words which can be included in the valid file name
    # we are doing this because if we donot filter out bad words then we receive 
    # an error on windows >:( 
    valid_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
    # here we are looping over the dictionary 
    for k,i in enumerate(result):
        # and printing the results on screen
        songTitle = ''.join(c for c in result[i]['title'] if c in valid_chars)
        Artist = ''.join(c for c in result[i]['uploader'] if c in valid_chars)
        print str(k+1) + ": "+songTitle+" --by-- " +Artist

    # here we are asking the user which song he wants to download
    user_choice = raw_input('\nEnter the Song ID you wish to download or (q) to exit: ')

    #Exit if choice is empty or q
    if user_choice == "" or user_choice == "q": exit() 

    # here we are running the extract_data method according to the user_choice variable
    extract_data(result[int(user_choice)]['url'],result[int(user_choice)]['id'],result[int(user_choice)]['title'])

    # looping over the final results received after resolving the url
    for i in final_result: 
        try:
            downloader(i['url'],i['title']+".mp3")
        except KeyboardInterrupt: #If we are interrupted by the user
            print "\nDownload cancelled by the user. "
    sys.exit()

def for_user():
     # we are asking the user which song does he want to download.
    song = raw_input("[Soundcloud-dl]  Which user do you want?\t")
    print "Searching for '%s'..."%(song)
    
    # here we are running the search method using the given query
    user_song_search(song)
    
    #default dictionary for holding the results
    result = {}

    # a variable simply to keep track of the songs
    # this variable will allows us to retrieve back the song which the user demands.
    count = 1

    # simply looping over the tracks variable produced by song_search method and assigning it to a dictionary
    for i in tracks:    
        #another dictionary for holding all the results for a specific song
        result[count] = {}
        result[count]['id'] = i.id
        result[count]['title'] = i.title
        result[count]['uploader'] = i.user['username']
        result[count]['duration'] = convertTime(i.duration)
        result[count]['size'] = convertSize(i.original_content_size)
        result[count]['url'] = i.permalink_url 

        # here we are incrementing the count variable by 1 everytime the loop runs
        count += 1

    valid_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
    # here we are looping over the dictionary 
    for k,i in enumerate(result):
        # and printing the results on screen
        songTitle = ''.join(c for c in result[i]['title'] if c in valid_chars)
        Artist = ''.join(c for c in result[i]['uploader'] if c in valid_chars)
        print str(k+1) + ": "+songTitle+" --by-- " +Artist

    # here we are asking the user which song he wants to download
    user_choice = raw_input('\n[Soundcloud-dl]  Enter the Song ID you wish to download or (q) to exit or (all) to download all songs: ')

    #Exit if choice is empty or q
    if user_choice == "" or user_choice == "q": 
        sys.exit() 
    elif user_choice == "all":
        for count,i in enumerate(result):
            try:
                extract_data(result[i]['url'],result[i]['id'],result[i]['title'])
                for i in final_result: 
                    downloader(i['url'],i['title']+".mp3")
                print "[Soundcloud-dl]  Downloaded %s songs\n" %(str(count+1))
            except KeyboardInterrupt: #If we are interrupted by the user
                print "\n[Soundcloud-dl]  Download cancelled by the user. "    
                sys.exit()
    else:
        # here we are running the extract_data method according to the user_choice variable
        extract_data(result[int(user_choice)]['url'])

        # looping over the final results received after resolving the url
        for i in final_result: 
            try:
                downloader(i['url'],i['title']+".mp3")
            except KeyboardInterrupt: #If we are interrupted by the user
                print "\n[Soundcloud-dl]  Download cancelled by the user. "
        sys.exit()

def for_url():
    # we are asking the user which song does he want to download.
    song = raw_input("[Soundcloud-dl]  Which url do you want to download?\t")
    print "[Soundcloud-dl]  Extracting info about the url..."
    final_result = single_url(song)
    url = final_result['url']
    title = final_result['title']
    try:
        downloader(url,title+".mp3")
    except KeyboardInterrupt: #If we are interrupted by the user
        print "\n[Soundcloud-dl]  Download cancelled by the user. "
    sys.exit()


# this tells us weather the script was directly run or not.
# If it is directly run then the code bellow this comment executes.
if __name__ == '__main__':
    print entrystring

    # we are asking the user that whether he wants to search for a song or a user
    print "[Soundcloud-dl]  Do you want to search for a song or download the songs by a specific user or want to download a song by giving it's url ? Type in 'song' or 'user' or 'url' according to your requirement."
    what = raw_input("[Soundcloud-dl]  Your choice?\t")

    # here we are using a simple for loop to check whether the user typed song, user or anything else.
    # And after that we are running the specified functions for each choice
    if what == "song" :
        for_song()
    elif what == "user":
        for_user()
    elif what == "url":
        for_url()
    else:
        print "[Soundcloud-dl]  your choice was wrong please run the program again\n"
        sys.exit()

   