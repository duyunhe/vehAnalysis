# -*- coding: utf-8 -*-
# @Time    : 2019/10/18 9:52
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : history.py


import cx_Oracle
from collections import defaultdict
import numpy as np
from map_info.readMap import MapInfo


def main():
    try:
        conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
        cur = conn.cursor()
        sql = "select rid, speed, ort, cnt from tb_road_speed_pre"
        cur.execute(sql)
        speed = defaultdict(list)
        for item in cur:
            rid, spd, ort, cnt = item
            speed[(rid, ort)].append((spd, cnt))
        tup_list = []
        for ln, spd_list in speed.items():
            t, w = 0, 0
            for spd, cnt in spd_list:
                t, w = t + spd * cnt, w + cnt
            ln_spd = t / w
            rid, ort = ln
            tup_list.append((rid, ort, ln_spd, w))
        sql = "delete from tb_road_his_speed"
        cur.execute(sql)

        sql = "insert into tb_road_his_speed (rid, ort, speed, cnt) values(:1, :2, :3, :4)"
        cur.executemany(sql, tup_list)
        conn.commit()
        cur.close()
        conn.close()
    except cx_Oracle.DatabaseError:
        print "oracle error"


def stat_def():
    conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
    cur = conn.cursor()
    sql = "select rid, speed, cnt, dbtime from tb_road_speed_pre"
    cur.execute(sql)
    spd_dict = defaultdict(list)
    for item in cur:
        rid, spd, cnt, db_time = item
        spd_dict[rid].append((spd, cnt))

    tup_list = []
    for rid, info_list in spd_dict.items():
        spd_list, cnt_list = zip(*info_list)
        med = np.median(spd_list)
        mad = np.median(np.abs(spd_list - med))
        lower_limit, upper_limit = med - 3 * mad, med + 3 * mad
        # print lower_limit, upper_limit
        valid_list = []
        cnt = 0
        for i, spd in enumerate(spd_list):
            if lower_limit <= spd <= upper_limit:
                valid_list.append(spd)
                cnt += cnt_list[i]
            # else:
            #     print spd
        avg = np.mean(valid_list)
        tup_list.append((rid, avg, cnt))
    sql = "delete from tb_road_his_speed"
    cur.execute(sql)
    sql = "insert into tb_road_his_speed (rid, speed, cnt) values(:1, :2, :3)"
    cur.executemany(sql, tup_list)
    conn.commit()
    cur.close()
    conn.close()


def def_speed(mi=None):
    if mi is None:
        mi = MapInfo("../map_info/hz3.db")
    rm = mi.road_map
    spd_dict = {}
    # 确保每一条道路都有值
    for k, v in rm.items():
        spd_dict[v] = 40
    try:
        conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
        cur = conn.cursor()
        sql = "select rid, speed, cnt from tb_road_his_speed"
        cur.execute(sql)
        tup_list = []
        for item in cur:
            rid, speed, cnt = item
            if cnt < 100 and speed < 20:
                speed = 20
            if speed > 70:
                speed = 70
            spd_dict[rid] = speed
        for rid, speed in spd_dict.items():
            tup_list.append((rid, speed))
        sql = "delete from tb_road_def_speed"
        cur.execute(sql)
        sql = "insert into tb_road_def_speed values(:1,:2)"
        cur.executemany(sql, tup_list)
        conn.commit()
        cur.close()
        conn.close()
    except cx_Oracle.DatabaseError:
        print "oracle error"


if __name__ == '__main__':
    stat_def()
    def_speed()
