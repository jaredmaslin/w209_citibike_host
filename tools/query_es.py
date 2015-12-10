#!/usr/bin/python

from elasticsearch import Elasticsearch
import json
import re
import sys

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
    query = '{\
                "query":\
                {\
                    "filtered":\
                    {\
                        "query":{"match_all":{}},\
                        "filter":\
                        {\
                            "bool": \
                            {'
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
    
    for d in res['aggregations'][json_ID_field]['buckets']:
        #FINAL OUTPUT in the format of {station_id, count}
        print "{},{}".format(d['key'],d['doc_count'])
    #print res['hits']['total']


def main():

    if len(sys.argv) < 13:
        print 'not enough args given'
        sys.exit(1)
    #get user input
    heavy_rain=sys.argv[1] # 1 or 0
    heavy_snow=sys.argv[2] # 1 or 0
    too_windy=sys.argv[3] # 1 or 0
    too_hot=sys.argv[4] # 1 or 0
    too_cold=sys.argv[5] # 1 or 0
    extreme_weather=sys.argv[6] # 1 or 0
    usertype=sys.argv[7] 
    gender=sys.argv[8] # 0, 1, or 2
    min_age=sys.argv[9]
    if min_age is None:
        min_age=0
    max_age=sys.argv[10]
    if max_age is None:
        max_age=0
    min_hour=sys.argv[11]
    if min_hour is None:
        min_hour=0
    max_hour=sys.argv[12]
    if max_hour is None:
        max_hour=23
    incoming=sys.argv[13] # 1 for incoming traffic (endID used), 0 for outgoing traffic (startID used)
    if incoming is None:
        incoming=1


    es = Elasticsearch(['localhost:9200'])
    dates = get_weather_data(es,heavy_rain=heavy_rain, heavy_snow=heavy_snow, too_windy=too_windy, 
                        too_hot=too_hot, too_cold=too_cold, extreme_weather=extreme_weather)
    if not dates:
        dates=[]

    get_trips_data(es, dates=dates, usertype=usertype, gender=gender, min_age=min_age, 
                    max_age=max_age, min_hour=min_hour, max_hour=max_hour, incoming=incoming)


if __name__ == '__main__':
    main()
