# -*- coding: utf-8 -*-
# @Time    : 2019/5/30 10:55
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : saveHisSpeed.py


import cx_Oracle


def save_speed(temp_speed):
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
