# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 16:12
# @Author  : yhdu@tongwoo.cn
# @简介    : 获取gps信息
# @File    : fetchData.py


import cx_Oracle
from datetime import timedelta, datetime
from coord import bl2xy
from geo import calc_dist
from time import clock
import json
import os
import redis
from taxiStruct import TaxiData
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "fetch.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


@debug_time
def get_gps_data(all_data=False, begin_time=None, end_time=None):
    if begin_time is None and end_time is None:
        begin_time = datetime(2018, 5, 1, 1, 0, 0)
        end_time = begin_time + timedelta(minutes=30)
    conn = cx_Oracle.connect('hz/hz@192.168.11.88:1521/orcl')
    if all_data:
        sql = "select px, py, speed_time, state, speed, carstate, direction, vehicle_num from " \
              "TB_GPS_1805 t where speed_time >= :1 " \
              "and speed_time < :2 and state = 1 order by speed_time "
    else:
        sql = "select px, py, speed_time, state, speed, carstate, direction, vehicle_num from " \
          "TB_GPS_1805 t where speed_time >= :1 " \
          "and speed_time < :2 and vehicle_num = '浙AT2081' and state = 1 order by speed_time "

    tup = (begin_time, end_time)
    cursor = conn.cursor()
    cursor.execute(sql, tup)
    veh_trace = {}
    for item in cursor.fetchall():
        lng, lat = map(float, item[0:2])
        if 119 < lng < 121 and 29 < lat < 31:
            px, py = bl2xy(lat, lng)
            state = int(item[3])
            stime = item[2]
            speed = float(item[4])
            car_state = int(item[5])
            ort = float(item[6])
            veh = item[7][-6:]
            # if veh != 'AT0956':
            #     continue
            taxi_data = TaxiData(veh, px, py, stime, state, speed, car_state, ort)
            try:
                veh_trace[veh].append(taxi_data)
            except KeyError:
                veh_trace[veh] = [taxi_data]
    new_dict = {}
    for veh, trace in veh_trace.iteritems():
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
                # print i, dist
                # i += 1
        new_dict[veh] = new_trace
    # print "all car:{0}, ave:{1}".format(len(static_num), len(trace) / len(static_num))
    cursor.close()
    conn.close()
    return new_dict


@debug_time
def trans2redis(trace_dict):
    conn = redis.Redis(host="192.168.11.229", port=6300, db=0)
    conn.flushdb()
    idx = 0
    for veh, trace in trace_dict.iteritems():
        msg = {}
        for data in trace:
            x, y, spd, speed_time, pos, load, ort = data.x, data.y, data.speed, \
                                                    data.stime, data.car_state, data.state, data.direction
            speed_time = speed_time.strftime("%Y-%m-%d %H:%M:%S")
            msg_dict = {'isu': veh, 'x': x, 'y': y, 'speed': spd, 'speed_time': speed_time, 'pos': pos, 'load': load,
                        'ort': ort}
            msg_json = json.dumps(msg_dict)
            msg_key = "{0}".format(idx)
            idx += 1
            msg[msg_key] = msg_json
        conn.mset(msg)


def redis2redis():
    conn = redis.Redis(host="192.168.11.229", port=6300, db=1)
    conn2 = redis.Redis(host="192.168.11.229", port=6300, db=2)
    conn2.flushdb()
    keys = conn.keys()
    res = conn.mget(keys)
    with conn2.pipeline() as p:
        for i, key in enumerate(keys):
            if res[i] is not None:
                p.set(key, res[i])
        p.execute()


def main():
    trace_dict = get_gps_data(False)
    trans2redis(trace_dict)


def get_gps_list(trace_dict):
    """
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
                # print data - last_data
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

    return trace_list


