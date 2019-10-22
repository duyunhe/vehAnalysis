# -*- coding: utf-8 -*-
# @Time    : 2019/5/30 10:55
# @Author  : yhdu@tongwoo.cn
# @简介    :
# @File    : saveHisSpeed.py


import cx_Oracle
from tti import get_tti_v0


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
    :param temp_speed: { (lid, fwd): speed }
    :param dt: datetime
    :param cnt_dict: { (lid, fwd) : cnt }
    :return: 
    """
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    tup_list = []
    for ln, speed in temp_speed.items():
        cnt = cnt_dict[ln]
        lid, fwd = ln[0], '1' if ln[1] else '0'
        tup_list.append((lid, speed, fwd, dt, cnt))
    ins_sql = "insert into tb_road_speed_pre (rid, speed, ort, dbtime, cnt) values(:1, :2, :3, :4, :5)"
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


def save_tti(temp_speed, cnt_dict, map_info, def_speed, db_time):
    """
    和save speed 一样
    :param temp_speed: 
    :param db_time: 
    :param cnt_dict: 
    :param map_info: readMap中的road_map 表示(lid, fwd(前进或后退))到rid的对应关系
    :param def_speed: {rid(int): speed(float)}
    :return: 
    """
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    tup_list = []
    for ln, speed in temp_speed.items():
        cnt = cnt_dict[ln]
        lid, fwd = ln[0], ln[1]
        rid = map_info.road_map[(lid, fwd)]
        try:
            ti = get_tti_v0(speed, def_speed[rid])
        except KeyError:
            ti = 0
        tup_list.append((rid, speed, cnt, ti, db_time))
    sql = "truncate table tb_road_speed"
    cur = conn.cursor()
    cur.execute(sql)
    sql = "insert into tb_road_speed values(:1, :2, :3, :4, :5, 1)"
    cur.executemany(sql, tup_list)
    conn.commit()
    cur.close()
    conn.close()
