import tweepy
import json
from elasticsearch import Elasticsearch, RequestsHttpConnection
#used for some timing
##import time

class StdOutListener(tweepy.StreamListener):
    #pass outfile connection to connector
    def __init__(self,outfile,outputtype):
        self.outfile=outfile
        self.outputtype=outputtype

    def on_data(self, data):
        # Twitter returns data in JSON format - we need to decode it first
        tweet = json.loads(data)
        #give some feedback that its running
        try:
            #only process Tweets with a location, would be better to filter stream with server side parmeter for Has:Geo
            #but I didn't see as an option
            # could be bounding box or coordinates
            if tweet['place'] is not None:
                if 'point'not in tweet['place']:
                    if 'bounding_box' in tweet['place']:
                        #convert bounding box if point not available - not as accurate but will get more data
                        lat_lon_est=mid_polygon(tweet['place']['bounding_box']['coordinates'])
                else:
                    lat_lon_est=tweet['place']['point']['coordinates']
                tweet['lat_lon']=lat_lon_est
                #toggle between saving to file for testing or uploading to elastic search
                if self.outputtype=='file':
                    with open(self.outfile, "a") as myfile:
                        myfile.write(json.dumps(tweet)+'\n')
                if self.outputtype=='elastic':
                    elasticstore(tweet)
                    print('Stored')

        except KeyError:
            # bypass for system messages
            pass


def elasticstore(tweet):
    host = 'search-savedtweets-aqycbsmsgwuclq7cgpbtdigtna.us-east-1.es.amazonaws.com'
    #optional auth parameted
    #awsauth = AWS4Auth(YOUR_ACCESS_KEY, YOUR_SECRET_KEY, REGION, 'es')
    #establish connection to Elasticsearch
    es = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        #http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )


    #index tweet in ES
    es.index(index='savedtweets', doc_type='tweet', body=tweet)


def load_data(es):
    #legacy from when I initially loaded from file
    lines = [json.loads(line.rstrip('\n')) for line in open('tweet_archive.json')]
    for i,line in enumerate(lines):
        res=es.index(index='savedtweets', doc_type='tweet', id=i, body=line)
        print res


def avg(l):
    return sum(l) / float(len(l))

def mid_polygon(poly):
    #turns bounding boxes to a point in the middle of the box
    #flip lat and long and average sides of bounding box
    poly_lat=[poly[0][0][1],poly[0][1][1],poly[0][2][1],poly[0][3][1]]
    poly_lon=[poly[0][0][0],poly[0][1][0],poly[0][2][0],poly[0][3][0]]
    return (avg(poly_lat),avg(poly_lon))

def load_creds(credloc):
    #load keys from key file
    with open(credloc) as data_file:
        data = json.load(data_file)
    return data


def open_twitter(args,creds,outfile,outputtype):
    #open a stream to twitter based on keyword arguments
    l = StdOutListener(outfile,outputtype)
    auth = tweepy.OAuthHandler(creds['twitter_key'], creds['twitter_secret'])
    auth.set_access_token(creds['twitter_access_token'], creds['twitter_token_secret'])
    stream = tweepy.Stream(auth, l)
    #subscribe to terms on stream
    stream.filter(track=args['terms'])
    return l

def main():
    #load credentials
    creds=load_creds('../cred/keys.txt')
    args={"terms":["sun","sunny","LOL"]}
    #open connection
    #archive type should file or elastic - determines location of tweet
    conn=open_twitter(args,creds,'tweet_archive.json','elastic')


if '__name__'!='main':
    main()