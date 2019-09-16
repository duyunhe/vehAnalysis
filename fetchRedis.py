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
from geo import calc_dist


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
    conn = redis.Redis(host="192.168.11.229", port=6300, db=2)
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
                car_state = js_data['pos']
                ort = js_data['ort']
                if car_state == 1:
                    continue

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


def get_gps_list(trace_dict):
    """
    filter original data
    :param trace_dict: 
    :return: 
    """
    trace_list = []
    for veh, trace in trace_dict.iteritems():
        new_trace = []
        last_data = None
        for data in trace:
            esti = True
            if last_data is not None:
                dist = calc_dist([data.x, data.y], [last_data.x, last_data.y])
                # 过滤异常
                if data.car_state == 1:  # 非精确
                    esti = False
                elif dist < 10:  # GPS的误差在10米，不准确
                    esti = False
            last_data = data
            if esti:
                new_trace.append(data)
        last_data = None
        x_trace = []
        for data in new_trace:
            if last_data is not None:
                itv = data - last_data
                if itv > 180:
                    if len(x_trace) > 1:
                        trace_list.append(x_trace)
                    x_trace = [data]
                else:
                    x_trace.append(data)
            else:
                x_trace.append(data)
            last_data = data
        if len(x_trace) > 1:
            trace_list.append(x_trace)
    pt_cnt = 0
    for trace in trace_list:
        pt_cnt += len(trace)
    return trace_list, pt_cnt
