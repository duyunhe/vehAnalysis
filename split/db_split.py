# -*- coding: utf-8 -*-
# @Time    : 2019/9/6 15:46
# @Author  : 
# @简介    : 
# @File    : db_split.py

import cx_Oracle
from collections import defaultdict
import os
from copy import copy
from time import clock
from datetime import datetime, timedelta
from meter_analysis import get_meter_data, get_offset
from trace_m import trace_split_off
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.AL32UTF8'


veh_trace = {}       # restore last list in history trace for each vehicle


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "fetch.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


def get_cbid():
    conn_db = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    cur = conn_db.cursor()
    sql = "select max(cbid) from tb_gps_trace"
    max_id = 0
    cur.execute(sql)
    for item in cur:
        max_id = item[0]
    cur.close()
    try:
        max_id = int(max_id)
    except TypeError:
        max_id = 0
    conn_db.close()
    return max_id


def save_db(conn, isu, cbid, state, data_list, dist, ks):
    # conn = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    tup_list = []
    for data in data_list:
        tup = (isu, data.px, data.py, data.speed_time, state, cbid)
        tup_list.append(tup)
    sql = "insert into tb_gps_trace (vhic, longi, lati, speed_time, state, cbid) values(:1, :2, :3, :4, :5, :6)"
    cur = conn.cursor()
    cur.executemany(sql, tup_list)
    conn.commit()

    sql = "insert into tb_area_trace (vhic, dep_longi, dep_lati, dest_longi, dest_lati, dep_time, dest_time, " \
          "state, cbid, dist, empty_dist) values(:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11)"
    tup = (isu, data_list[0].px, data_list[0].py, data_list[-1].px, data_list[-1].py, data_list[0].speed_time,
           data_list[-1].speed_time, state, cbid, dist, ks)
    cur.execute(sql, tup)
    conn.commit()
    cur.close()
    # conn.close()


class TaxiData(object):
    def __init__(self, px, py, speed_time, state):
        self.px, self.py, self.speed_time = px, py, speed_time
        self.state = state


def split_data(data_list):
    last_state = -1
    trace, trace_list = [], []
    for data in data_list:
        if data.state == last_state:
            trace.append(data)
        else:
            if len(trace) > 1:
                trace_list.append(trace)
            trace = [data]
        last_state = data.state
    if len(trace) > 0:
        trace_list.append(trace)
    return trace_list


@debug_time
def proc_data_v1(cur_dict, off_dict, meter_dict):
    global veh_trace
    cbid = get_cbid()
    conn = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    cur_cnt = 0

    # 去掉那些10101重复的情况
    for veh, data_list in cur_dict.items():
        for i, data in enumerate(data_list):
            if 0 < i < len(data_list) - 1:
                if data_list[i].state == 0 and data_list[i - 1].state == 1 and data_list[i + 1].state == 1:
                    data_list[i].state = 1
                if data_list[i].state == 1 and data_list[i - 1].state == 0 and data_list[i + 1].state == 0:
                    data_list[i].state = 0
        try:
            all_list = copy(veh_trace[veh])
            all_list.extend(data_list)
        except KeyError:
            all_list = data_list
        # here, change split methods
        try:
            meter_list = meter_dict[veh]
            try:
                off_time = off_dict[veh]
                trace_list = trace_split_off(meter_list, data_list, off_time)
                for trace in trace_list[:-1]:
                    state = trace.state
                    save_db(conn, veh, cbid, state, trace.trace, trace.dist, trace.ks)
                    cbid += 1
                    cur_cnt += 1
            except KeyError:
                off_time = None
                print veh, "no off"
                continue
        except KeyError:
            print veh, "no meter"
            continue
        veh_trace[veh] = trace_list[-1].trace
    print "meter final", cur_cnt
    conn.close()


@debug_time
def get_data(bt, et):
    conn = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    cur = conn.cursor()
    y, m = bt.year % 100, bt.month
    table_name = "hz.tb_gps_{0}{1:02d}".format(y, m)
    sql = "select vehicle_num, px, py, state, speed_time from {0} " \
          "where carstate = '0' and speed_time >= :1 " \
          "and speed_time < :2 order by speed_time".format(table_name)
    tup = (bt, et)
    cur.execute(sql, tup)
    cur_dict = defaultdict(list)
    for item in cur:
        veh, px, py, state, speed_time = item[:]
        veh = veh[3:]
        if veh[:2] != "AT":
            continue
        state = int(state)
        if 110 < px < 130 and 20 < py < 40:
            taxi_data = TaxiData(px, py, speed_time, state)
            cur_dict[veh].append(taxi_data)
    cur.close()
    conn.close()
    # print len(cur_dict)
    return cur_dict


def delete_data():
    conn = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    cur = conn.cursor()
    sql = "truncate table tb_area_trace"
    cur.execute(sql)
    conn.commit()
    sql = "truncate table tb_gps_trace"
    cur.execute(sql)
    conn.commit()
    conn.close()


def main():
    delete_data()
    bt = datetime(2018, 5, 1, 0)
    ft = datetime(2018, 5, 5, 0)
    while bt < ft:
        et = bt + timedelta(hours=1)
        meter_dict = get_meter_data(bt, et)
        off_dict = get_offset(bt)
        cur_dict = get_data(bt, et)
        bt += timedelta(hours=1)
        proc_data_v1(cur_dict, off_dict, meter_dict)


if __name__ == '__main__':
    main()
