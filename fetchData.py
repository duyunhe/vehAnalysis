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
def get_all_data(all_data=False, begin_time=None, end_time=None):
    if begin_time is None and end_time is None:
        begin_time = datetime(2018, 5, 1, 12, 0, 0)
        end_time = begin_time + timedelta(minutes=60)
    conn = cx_Oracle.connect('hz/hz@192.168.11.88:1521/orcl')
    if all_data:
        sql = "select px, py, speed_time, state, speed, carstate, direction, vehicle_num from " \
              "TB_GPS_1805 t where speed_time >= :1 " \
              "and speed_time < :2 order by speed_time "
    else:
        sql = "select px, py, speed_time, state, speed, carstate, direction, vehicle_num from " \
          "TB_GPS_1805 t where speed_time >= :1 " \
          "and speed_time < :2 and vehicle_num = '浙ALT002' order by speed_time "

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
            veh_head = veh[:2]
            # if veh_head != 'AT' and veh_head != 'AL':
            #     continue
            # if veh != 'AT0956':
            #     continue
            taxi_data = TaxiData(veh, px, py, stime, state, speed, car_state, ort)
            try:
                veh_trace[veh].append(taxi_data)
            except KeyError:
                veh_trace[veh] = [taxi_data]
    cursor.close()
    conn.close()
    return veh_trace


def get_all_on():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cur = conn.cursor()
    sql = "select vehicle_num, during_time from tb_during_on_time"
    cur.execute(sql)
    veh_dict = {}
    for item in cur:
        veh, on_time = item
        veh_dict[veh] = on_time
    cur.close()
    conn.close()
    return veh_dict


@debug_time
def get_formal_data(all_data=False, begin_time=None, end_time=None):
    conn = cx_Oracle.connect('hzczdsj/tw85450077@192.168.0.80:1521/orcl')
    on_dict = get_all_on()
    if all_data:
        sql = "select px, py, speed_time, state, carstate, vehicle_num from " \
              "TB_GPS_TEMP t where speed_time >= :1 " \
              "and speed_time < :2 and carstate = 0 order by speed_time "
    else:
        sql = "select px, py, speed_time, state, carstate, vehicle_num from " \
          "TB_GPS_TEMP t where speed_time >= :1 " \
          "and speed_time < :2 and vehicle_num = '浙ALT002' and state = 1 order by speed_time "

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
            speed = 0
            car_state = int(item[4])
            ort = 0
            veh = item[5][-6:]
            veh_head = veh[:2]
            # if veh_head != 'AT' and veh_head != 'AL':
            #     continue
            # if veh in on_set:
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
        try:
            total_itv = on_dict[veh]
        except KeyError:
            total_itv = 0

        for data in trace:
            esti = True
            if data.state == 0:
                esti = False
            if last_data is not None:
                dist = calc_dist([data.x, data.y], [last_data.x, last_data.y])
                # 过滤异常
                if dist < 10:  # GPS的误差在10米，不准确
                    esti = False
                if data.state == 0:
                    total_itv = 0
                else:
                    total_itv += data - last_data
            last_data = data
            if esti:
                new_trace.append(data)
                # print i, dist
                # i += 1
        # 假如重车时间太长（超过两个小时），那么可能存在问题
        if total_itv < 7200:
            new_dict[veh] = new_trace
        on_dict[veh] = total_itv
    # print "all car:{0}, ave:{1}".format(len(static_num), len(trace) / len(static_num))
    cursor.close()
    conn.close()
    save_all_on(on_dict)
    return new_dict, on_dict


def save_all_on(on_dict):
    """
    :param on_dict: {veh: during_time(seconds)} 
    :return: 
    """
    conn = cx_Oracle.connect('hz/hz@192.168.11.88:1521/orcl')
    cursor = conn.cursor()
    sql = "delete from tb_during_on_time"
    cursor.execute(sql)
    tup_list = []
    sql = "insert into tb_during_on_time values(:1,:2)"
    for veh, on_time in on_dict.items():
        tup_list.append((veh, on_time))
    cursor.executemany(sql, tup_list)
    conn.commit()
    cursor.close()
    conn.close()


@debug_time
def get_gps_data(all_data=False, begin_time=None, end_time=None):
    """
    历史数据，采纳两小时的GPS数据
    :param all_data: 
    :param begin_time: 
    :param end_time: 
    :return: 
    """
    if begin_time is None and end_time is None:
        begin_time = datetime(2018, 5, 1, 12, 0, 0)
        end_time = begin_time + timedelta(minutes=60)
    conn = cx_Oracle.connect('hz/hz@192.168.11.88:1521/orcl')
    if all_data:
        sql = "select px, py, speed_time, state, speed, carstate, direction, vehicle_num from " \
              "TB_GPS_1805 t where speed_time >= :1 " \
              "and speed_time < :2 and carstate = '0' order by speed_time "
    else:
        sql = "select px, py, speed_time, state, speed, carstate, direction, vehicle_num from " \
          "TB_GPS_1805 t where speed_time >= :1 " \
          "and speed_time < :2 and vehicle_num = '浙AT7484' and carstate = '0' order by speed_time "

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
            veh_head = veh[:2]
            # if veh_head != 'AT' and veh_head != 'AL':
            #     continue
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
        on_cnt, off_cnt = 0, 0
        for data in trace:
            esti = True
            if data.state == 1:
                on_cnt += 1
            else:
                off_cnt += 1
            if last_data is not None:
                dist = calc_dist([data.x, data.y], [last_data.x, last_data.y])
                # 过滤异常
                if data.state == 0:
                    esti = False
                if dist < 10:  # GPS的误差在10米，不准确
                    esti = False
            last_data = data
            if esti:
                new_trace.append(data)
                # print i, dist
                # i += 1
        per = float(on_cnt) / (on_cnt + off_cnt)
        if per > 0.9:
            continue
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


def get_gps_list(trace_dict, history=False):
    """
    :param trace_dict: 
    :param history: 是否统计历史数据
    :return: 
    """
    trace_list = []
    pt_cnt = 0
    for veh, trace in trace_dict.iteritems():
        new_trace = trace
        last_data = None
        x_trace = []
        for data in new_trace:
            if last_data is not None:
                itv = data - last_data
                if itv > 300:
                    if len(x_trace) > 1:
                        dist = calc_dist(x_trace[0], x_trace[-1])
                        if history:
                            if dist > 1000:
                                trace_list.append(x_trace)
                        else:
                            trace_list.append(x_trace)
                    x_trace = [data]
                else:
                    x_trace.append(data)
            else:
                x_trace.append(data)
            last_data = data
        if len(x_trace) > 1:
            dist = calc_dist(x_trace[0], x_trace[-1])
            if history:
                if dist > 1000:
                    trace_list.append(x_trace)
            else:
                trace_list.append(x_trace)
    for trace in trace_list:
        pt_cnt += len(trace)

    return trace_list, pt_cnt


def get_def_speed():
    conn = cx_Oracle.connect('hz/hz@192.168.11.88:1521/orcl')
    cursor = conn.cursor()
    sql = "select rid, speed from tb_road_def_speed"
    cursor.execute(sql)
    def_speed = {}
    for item in cursor:
        rid, speed = item
        def_speed[rid] = speed
    cursor.close()
    conn.close()
    return def_speed
