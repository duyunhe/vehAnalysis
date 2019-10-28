# -*- coding: utf-8 -*-
# @Time    : 2019/5/30 10:55
# @Author  : yhdu@tongwoo.cn
# @简介    :
# @File    : saveHisSpeed.py


import cx_Oracle
from tti import get_tti_v1
from time import clock
import numpy as np


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "saveHisSpeed.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


def save_speed_detail(temp_speed):
    """
    :param temp_speed: { veh: [LineSpeed, ...] }
    :return: 
    """
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    tup_list = []
    for ln, speed_list in temp_speed.items():
        lid = ln.lid
        ort = 0 if ln.fwd else 1
        for speed_item in speed_list:
            spd, dist, veh, date = speed_item[:]
            tup = (lid, ort, spd, veh, dist, date)
            tup_list.append(tup)
    ins_sql = "insert into tb_road_speed_detail values(:1, :2, :3, :4, :5, :6)"
    cur = conn.cursor()
    cur.executemany(ins_sql, tup_list)
    conn.commit()
    cur.close()
    conn.close()


def save_speed(temp_speed, dt, cnt_dict):
    """
    :param temp_speed: { rid: speed }
    :param dt: datetime
    :param cnt_dict: { rid : cnt }
    :return: 
    """
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    tup_list = []
    for rid, speed in temp_speed.items():
        cnt = cnt_dict[rid]
        tup_list.append((rid, speed, dt, cnt))
    ins_sql = "insert into tb_road_speed_pre (rid, speed, dbtime, cnt) values(:1, :2, :3, :4)"
    cur = conn.cursor()
    cur.executemany(ins_sql, tup_list)
    conn.commit()
    cur.close()
    conn.close()


def truncate_table():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cur = conn.cursor()
    sql = "truncate table tb_road_speed_pre"
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def get_highway():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    sql = "select rid from tb_highway"
    cursor.execute(sql)
    rid_list = []
    for item in cursor:
        rid = item[0]
        rid_list.append(rid)
    cursor.close()
    conn.close()
    return rid_list


def get_main_road():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    sql = "select rid from tb_top100"
    cursor.execute(sql)
    rid_list = []
    for item in cursor:
        rid = item[0]
        rid_list.append(rid)
    cursor.close()
    conn.close()
    return rid_list


def save_tti(temp_speed, cnt_dict, def_speed_dict, db_time, history=False):
    """
    和save speed 一样
    :param temp_speed: {rid: speed}
    :param db_time: 
    :param cnt_dict: 
    :param def_speed_dict: {rid(int): speed(float)}
    :param history: 是否要记录到历史数据库中，包括tb_road_speed_his tb_traffic_index
    :return: 
    """
    fast_road = get_highway()
    main_road = get_main_road()
    fast_set, main_set = set(fast_road), set(main_road)
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    tup_list = []
    tti_list, fast_list, main_list = [], [], []
    for rid, def_speed in def_speed_dict.items():
        try:
            cnt = cnt_dict[rid]
            speed = temp_speed[rid]
            if rid in fast_set:
                fast_list.append(speed)
            elif rid in main_set:
                main_list.append(speed)
        except KeyError:
            cnt = 0
            speed = def_speed_dict[rid]
        # lid, fwd = ln[0], ln[1]
        # rid = map_info.road_map[(lid, fwd)]
        ti = get_tti_v1(speed, def_speed)
        if rid in main_set or rid in fast_set:
            tti_list.append(ti)
        tup_list.append((rid, speed, cnt, ti, db_time))
    sql = "truncate table tb_road_speed"
    cur = conn.cursor()
    cur.execute(sql)
    sql = "insert into tb_road_speed values(:1, :2, :3, :4, :5, 1)"
    cur.executemany(sql, tup_list)
    if history:
        sql = "insert into tb_road_speed_his values(:1, :2, :3, :4, :5, 1)"
        cur.executemany(sql, tup_list)
        tti, fast_speed, main_speed = np.mean(tti_list), np.mean(fast_list), np.mean(main_list)
        congest_cnt, all_cnt = 0, len(tti_list)
        for ti in tti_list:
            if ti >= 6.0:
                congest_cnt += 1
        congest_ratio = 1.0 * congest_cnt / all_cnt         # 拥堵指数
        tup = (tti, fast_speed, main_speed, congest_ratio, db_time)
        sql = "insert into tb_traffic_index values(:1, :2, :3, :4, :5)"
        cur.execute(sql, tup)

    conn.commit()
    cur.close()
    conn.close()
