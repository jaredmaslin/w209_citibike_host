#!/usr/bin/python
#
# Flask server, woo!
#

from flask import Flask, request, redirect, url_for, send_from_directory
from elasticsearch import Elasticsearch
import json, csv
import re
import sys


# Setup Flask app.
app = Flask(__name__)
app.debug = True

def get_weather_data(es, heavy_rain=None, heavy_snow=None, too_windy=None, 
                            too_hot=None, too_cold=None, extreme_weather=None):

        query = '{ "query": { "filtered": { "query":{"match_all":{}}, "filter": { "bool":  {'

        conditions=[]
        if heavy_rain is not None:
            conditions.append('"must": {"term": {"heavy_rain":'+str(heavy_rain)+'} }')
        if heavy_snow is not None:
            conditions.append('"must": {"term": {"heavy_snow":'+str(heavy_snow)+'} }')
        if too_windy is not None:
            conditions.append('"must": {"term": {"too_windy":'+str(too_windy)+'} }')
        if too_hot is not None:
            conditions.append('"must": {"term": {"too_hot":'+str(too_hot)+'} }')
        if too_cold is not None:
            conditions.append('"must": {"term": {"too_cold":'+str(too_cold)+'} }')
        if extreme_weather is not None:
            conditions.append('"must": {"term": {"extreme_weather":'+str(extreme_weather)+'} }')

        query = query + ",".join(conditions)
        
        query = query + "}}}}}"
        res = es.search(index="weather",
                        size=500,
                        body=query)
        
        dates=[]
        for hit in res['hits']['hits']:
            dates.append(hit['_source']['DATE'])
        #print("Matched %d days:" % res['hits']['total'])
        dates = map(lambda x:'"'+str(x)+'"',dates)
        return dates


def get_trips_data(es, dates=None, usertype=None, gender=None, min_age=0, max_age=99, min_hour=0, max_hour=23, incoming=1):
        query = '{ "query": { "filtered": { "query":{"match_all":{}}, "filter": { "bool": {'
        conditions=[]

        if dates is not None:
            conditions.append('"must": {"terms": {"date": ' + re.sub("\'","",str(dates)) + ' } }')
        if usertype is not None:
            conditions.append('"must": {"term": {"usertype":' + str(usertype) + '} }')
        if gender is not None:
            conditions.append('"must": {"term": {"gender":' + str(gender)+'} }')
        conditions.extend(['"must": {"range": {"age": { "gte": ' + str(min_age) + ', "lte":' + str(max_age)+'} } }',
                                                '"must": {"range": {"hour": { "gte":' + str(min_hour) + ', "lte": ' + str(max_hour) + '} } }'])

        if incoming == 1:
            query = query + ",".join(conditions) + '}}}},"aggregations":{"endID":{"terms":{"field":"endID","size":0}}}}'
            json_ID_field='endID'
        else:
            query = query + ",".join(conditions) + '}}}},"aggregations":{"startID":{"terms":{"field":"startID","size":0}}}}'
            json_ID_field='startID'

        res = es.search(index="trips",
                        size=10000,
                        body=query)
        
        fopen = open('static/tmp_data/tmp_query_output.csv','w')
        for d in res['aggregations'][json_ID_field]['buckets']:
            #FINAL OUTPUT in the format of {station_id, count}
            fopen.write("{},{}\n".format(d['key'],d['doc_count']))
        #print res['hits']['total']
        fopen.close()


# Routes
@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)

#http://127.0.0.1:5000/query_es?heavy_rain=0&heavy_snow=0&too_windy=0&too_hot=0&too_cold=0&extreme_weather=0&usertype=1&gender=0&min_age=20&max_age=30&min_hour=0&max_hour=23&incoming=1
@app.route('/query_es', methods=['GET'])
def query_es():
    #get user input
    heavy_rain=request.args.get('heavy_rain') # 1 or 0
    heavy_snow=request.args.get('heavy_snow') # 1 or 0
    too_windy=request.args.get('too_windy') # 1 or 0
    too_hot=request.args.get('too_hot') # 1 or 0
    too_cold=request.args.get('too_cold') # 1 or 0
    extreme_weather=request.args.get('extreme_weather') # 1 or 0
    usertype=request.args.get('usertype')
    gender=request.args.get('gender') # 0, 1, or 2
    min_age=request.args.get('min_age')
    if min_age is None:
        min_age=0
    max_age=request.args.get('max_age')
    if max_age is None:
        max_age=0
    min_hour=request.args.get('min_hour')
    if min_hour is None:
        min_hour=0
    max_hour=request.args.get('max_hour')
    if max_hour is None:
        max_hour=23
    incoming=request.args.get('incoming') # 1 for incoming traffic (endID used), 0 for outgoing traffic (startID used)
    if incoming is None:
        incoming=1


    #es = Elasticsearch(['localhost:9200'])
    es = Elasticsearch(['https://search-w209-tma-gffjjisnofefdcomwzogolkeba.us-east-1.es.amazonaws.com/'])
    dates = get_weather_data(es,heavy_rain=heavy_rain, heavy_snow=heavy_snow, too_windy=too_windy, 
                        too_hot=too_hot, too_cold=too_cold, extreme_weather=extreme_weather)
    if not dates:
        dates=[]

    get_trips_data(es, dates=dates, usertype=usertype, gender=gender, min_age=min_age, 
                    max_age=max_age, min_hour=min_hour, max_hour=max_hour, incoming=incoming)

    # dump data in csv file into json object
    fopen = open('static/tmp_data/tmp_query_output.csv','r')

    # Open the CSV  
    # Change each fieldname to the appropriate field name.
    reader = csv.DictReader( fopen, fieldnames = ( "stationId","count"))  
    # Parse the CSV into JSON  
    out = json.dumps( [ row for row in reader ] )  
    fopen.close()
    #return 'Please check the tmp query document at static/tmp_data/tmp_query_output.csv'
    return out

def aggregate_trip_by_date(es, stationId=None, dates=None, usertype=None, gender=None, min_age=0, max_age=99, min_hour=0, max_hour=23, incoming=1):
        query = '{ "query": { "filtered": { "query":{"match_all":{}}, "filter": { "bool": {'
        conditions=[]

        if dates is not None:
            conditions.append('"must": {"terms": {"date": ' + re.sub("\'","",str(dates)) + ' } }')
        if usertype is not None:
            conditions.append('"must": {"term": {"usertype":' + str(usertype) + '} }')
        if gender is not None:
            conditions.append('"must": {"term": {"gender":' + str(gender)+'} }')
        conditions.extend(['"must": {"range": {"age": { "gte": ' + str(min_age) + ', "lte":' + str(max_age)+'} } }',
                                                '"must": {"range": {"hour": { "gte":' + str(min_hour) + ', "lte": ' + str(max_hour) + '} } }'])
        if incoming == 1:
            conditions.append('"must": {"term": {"endID":' + str(stationId)+'} }')
        else:
            conditions.append('"must": {"term": {"startID":' + str(stationId)+'} }')

        query = query + ",".join(conditions) + '}}}},"aggregations":{"date":{"terms":{"field":"date","size":0}}}}'
        res = es.search(index="trips",
                        size=10000,
                        body=query)
        json_ID_field='date'
        #print res['aggregations'][json_ID_field]['buckets']
        fopen = open('static/tmp_data/tmp_trip_count_by_date.csv','w')
        for d in res['aggregations'][json_ID_field]['buckets']:
            #FINAL OUTPUT in the format of {station_id, count}
            fopen.write("{},{}\n".format(d['key_as_string'],d['doc_count']))
        #print res['hits']['total']
        fopen.close()


@app.route('/query_daily_trip_count', methods=['GET'])
def query_daily_trip_count():

    #get user input
    station_id=request.args.get('station_id')
    heavy_rain=request.args.get('heavy_rain') # 1 or 0
    heavy_snow=request.args.get('heavy_snow') # 1 or 0
    too_windy=request.args.get('too_windy') # 1 or 0
    too_hot=request.args.get('too_hot') # 1 or 0
    too_cold=request.args.get('too_cold') # 1 or 0
    extreme_weather=request.args.get('extreme_weather') # 1 or 0
    usertype=request.args.get('usertype')
    gender=request.args.get('gender') # 0, 1, or 2
    min_age=request.args.get('min_age')
    if min_age is None:
        min_age=0
    max_age=request.args.get('max_age')
    if max_age is None:
        max_age=0
    min_hour=request.args.get('min_hour')
    if min_hour is None:
        min_hour=0
    max_hour=request.args.get('max_hour')
    if max_hour is None:
        max_hour=23
    incoming=request.args.get('incoming') # 1 for incoming traffic (endID used), 0 for outgoing traffic (startID used)
    if incoming is None:
        incoming=1


    #es = Elasticsearch(['localhost:9200'])
    es = Elasticsearch(['https://search-w209-tma-gffjjisnofefdcomwzogolkeba.us-east-1.es.amazonaws.com/'])
    dates = get_weather_data(es,heavy_rain=heavy_rain, heavy_snow=heavy_snow, too_windy=too_windy, 
                        too_hot=too_hot, too_cold=too_cold, extreme_weather=extreme_weather)
    if not dates:
        # no dates matches the requirement
        return None

    aggregate_trip_by_date(es, stationId=station_id, dates=dates, usertype=usertype, gender=gender, min_age=min_age, 
                    max_age=max_age, min_hour=min_hour, max_hour=max_hour, incoming=incoming)

    # dump data in csv file into json object
    fopen = open('static/tmp_data/tmp_trip_count_by_date.csv','r')

    # Open the CSV  
    # Change each fieldname to the appropriate field name.
    reader = csv.DictReader( fopen, fieldnames = ( "date","count"))  
    # Parse the CSV into JSON  
    out = json.dumps( [ row for row in reader ] )  
    fopen.close()
    #return 'Please check the tmp query document at static/tmp_data/tmp_query_output.csv'
    return out



if __name__ == '__main__':
    #app.run(host='0.0.0.0')
    app.run(host='127.0.0.1')
