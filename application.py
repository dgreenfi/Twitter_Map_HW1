from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify

#from datetime import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection
#import json

application = Flask(__name__)

#@application.route('/')
#def index():
#    return render_template('index.html',)

@application.route('/')
def index():
    application.logger.info('Map Query')
    #set default query
    if 'query' in request.args:
        query = request.args.get('query')
    else:
        query='LOL'
    #return tweets from elastic search
    locs=_callsearch(query)
    return render_template('index.html',q=query,tweet_array=locs)

def _callsearch(query):

    host = 'search-savedtweets-aqycbsmsgwuclq7cgpbtdigtna.us-east-1.es.amazonaws.com'
    es = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        #http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    f=es.search(index='savedtweets',q='text:'+query,size=500)
    locs=[]
    #return locations in javascript form
    for i,record in enumerate(f['hits']['hits']):
        locs.append([record['_source']['user']['screen_name'],record['_source']['lat_lon'][0],record['_source']['lat_lon'][1],i+1,record['_source']['text']])

    return locs

@application.route('/search')
def search():
    #useful for testing
    searchq = request.args.get('query')
    lat= request.args.get('lat')
    lon=request.args.get('lon')
    filterdist=request.args.get('dist')


    host = 'search-savedtweets-aqycbsmsgwuclq7cgpbtdigtna.us-east-1.es.amazonaws.com'
    es = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        #http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    # search params
    # query={
    #       "query": {
    #         "filtered": {
    #           "query": {
    #             "match_all": {}
    #           },
    #           "filter": {
    #             "geo_distance": {
    #               "distance": "20miles",
    #               "pin.location": {
    #                 "lat": 51.512497,
    #                 "lon": -0.052098
    #               }
    #             }
    #           }
    #         }
    #       }
    #     }


    f=es.search(index='savedtweets',body=query)
    return jsonify(f['hits'])

@application.errorhandler(500)
def internal_error(exception):
    #500 Error template
    application.logger.error(exception)
    return render_template('500.html',err=exception), 500

if __name__ == '__main__':
    application.run(debug=True)
