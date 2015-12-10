#!/bin/bash

#get user input
#    heavy_rain=sys.argv[1] # 1 or 0
#    heavy_snow=sys.argv[2] # 1 or 0
#    too_windy=sys.argv[3] # 1 or 0
#    too_hot=sys.argv[4] # 1 or 0
#    too_cold=sys.argv[5] # 1 or 0
#    extreme_weather=sys.argv[6] # 1 or 0
#    usertype=sys.argv[7] # User Type (Subscriber = 24-hour pass or 7-day pass user; Subscriber = Annual Member)
#    gender=sys.argv[8] # 0, 1, or 2 # Gender (Zero=unknown; 1=male; 2=female)
#    min_age=sys.argv[9]
#    max_age=sys.argv[10]
#    min_hour=sys.argv[11]
#    max_hour=sys.argv[12]
#    incoming=sys.argv[13] # 1 for incoming traffic (endID used), 0 for outgoing traffic (startID used)

python query_es.py 1 0 0 0 0 0 1 0 20 30 0 23 1 > output/query_HeavyRain_Subscriber_Male_Age20To30_Hour0To23_incoming.csv
python query_es.py 0 0 0 0 0 0 1 0 20 30 0 23 1 > output/query_GoodWeather_Subscriber_Male_Age20To30_Hour0To23_incoming.csv
python query_es.py 0 0 0 0 0 0 1 1 20 30 0 23 0 > output/query_GoodWeather_Subscriber_Male_Age20To30_Hour0To23_outgoing.csv
python query_es.py 0 0 0 0 0 0 1 1 30 40 0 23 1 > output/query_GoodWeather_Subscriber_Male_Age30To40_Hour0To23_incoming.csv
python query_es.py 0 0 0 0 0 0 1 1 20 30 0 7 0 > output/query_GoodWeather_Subscriber_Male_Age20To30_Hour0To7_outgoing.csv
python query_es.py 0 0 0 0 0 0 1 2 20 30 0 23 1 > output/query_GoodWeather_Subscriber_Female_Age20To30_Hour0To23_incoming.csv
python query_es.py 0 0 0 0 0 0 0 0 0 99 0 23 0 > output/query_GoodWeather_Customer_Unknown_AgeUnknown_Hour0To23_outgoing.csv
