# -*- coding: utf-8 -*-
# @Time    : 2019/5/30 14:49
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : orcl2Mongo.py


from fetchData import get_gps_data
from pymongo import MongoClient
from datetime import datetime, timedelta
from time import clock


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "mongo.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


@debug_time
def trans2mongo():
    bt = datetime(2018, 5, 1, 1)
    et = bt + timedelta(hours=4)
    trace_dict = get_gps_data(True, bt, et)
    client = MongoClient("mongodb://192.168.11.88:27017/")
    db = client['taxi']
    col = db['gps']
    col.delete_many({})
    data_list = []
    for veh, trace in trace_dict.items():
        for data in trace:
            data = data.__dict__
            stime = data['stime'].strftime("%Y-%m-%d %H:%M:%S")
            data['stime'] = stime
            data_list.append(data)
    col.insert_many(data_list)


@debug_time
def get_mongodb():
    client = MongoClient("mongodb://192.168.11.88:27017/")
    db = client['taxi']
    col = db['gps']
    data_list = []
    for data in col.find():
        data_list.append(data)
    print len(data_list)
    return data_list


get_mongodb()
