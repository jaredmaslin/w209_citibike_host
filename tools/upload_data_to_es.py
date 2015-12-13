#!/usr/bin/python

from elasticsearch import Elasticsearch
import json
import sys

def data_handler(infile, table_name, es):
    # json content of each line
    # open the file
    f_in = open(infile, 'r')
    # traverse through the file, first line is always the header line
    for i, line in enumerate(f_in):
        line = line.decode('utf-8', 'ignore')
        line_split = line.strip().split(',')
        if i == 0:
            header = line_split
            print header
        else:
            body = {}
            # format data into json format and create json body
            for idx in range(len(header)):
                body[str(header[idx])] = line_split[idx].strip()
            body = json.dumps(body)
            # Uploading to ElasticSearch
            retval = es.index(index = table_name, doc_type = 'db', id = i+1, body = body)

    f_in.close()


def main():
    #2.1.0 version
    #es = Elasticsearch(['localhost:9200'])
    #v1.7.3 version
    #es = Elasticsearch(['localhost:9201'])
    es = Elasticsearch(['https://search-w209-tma-gffjjisnofefdcomwzogolkeba.us-east-1.es.amazonaws.com/'])
    data_handler("data/weather.simplified.csv", "weather", es)
    data_handler("data/stations.csv", "stations", es)
    data_handler("data/trips.csv", "trips", es)

if __name__ == '__main__':
    main()
