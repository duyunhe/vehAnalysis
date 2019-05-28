# -*- coding: utf-8 -*-
# @Time    : 2019/5/27 17:13
# @Author  : yhdu@tongwoo.cn
# @简介    : 多进程用，无需xy调用dll
# @File    : fetchRedis.py


import redis
import json
from datetime import datetime
from taxiStruct import TaxiData, cmp_gps
from time import clock


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "fetch.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


@debug_time
def get_gps_data():
    conn = redis.Redis(host="192.168.11.229", port=6300, db=1)
    keys = conn.keys()
    new_trace = {}
    if len(keys) != 0:
        m_res = conn.mget(keys)
        veh_trace = {}
        static_num = {}
        for data in m_res:
            try:
                js_data = json.loads(data)
                px, py = js_data['x'], js_data['y']
                veh, str_time = js_data['isu'], js_data['speed_time']
                speed = js_data['speed']
                stime = datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")
                state = 1
                car_state = 0
                ort = js_data['ort']

                taxi_data = TaxiData(veh, px, py, stime, state, speed, car_state, ort)
                try:
                    veh_trace[veh].append(taxi_data)
                except KeyError:
                    veh_trace[veh] = [taxi_data]
                try:
                    static_num[veh] += 1
                except KeyError:
                    static_num[veh] = 1
            except TypeError:
                pass

        for veh, trace in veh_trace.iteritems():
            trace.sort(cmp_gps)
            new_trace[veh] = trace

    return new_trace
