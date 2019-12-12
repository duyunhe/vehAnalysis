# -*- coding: utf-8 -*-
# @Time    : 2019/10/28 10:23
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : top100.py


import cx_Oracle
from datetime import datetime, timedelta
from collections import defaultdict
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


def main():
    road_map, reverse_map = get_map()
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    dt = datetime(2019, 10, 30)
    bt = datetime(2019, 10, 28)
    sql = "select rid, sample_num from tb_road_speed_his where dbtime < :1 and dbtime >= :2"
    cursor.execute(sql, (dt, bt))
    cnt = defaultdict(int)
    for item in cursor:
        rid, s_num = item
        try:
            road_name = road_map[rid]
        except KeyError:
            continue
        cnt[road_name] += s_num
    a = sorted(cnt.items(), key=lambda x: x[1], reverse=True)
    t = a[:50]
    tup_list = []
    for item in t:
        name, c = item
        print name, c
        for rid in reverse_map[name]:
            tup_list.append((name, rid))
    # sql = "delete from tb_top100"
    # cursor.execute(sql)
    # sql = "insert into tb_top100 values(:1, :2)"
    # cursor.executemany(sql, tup_list)
    # conn.commit()
    cursor.close()
    conn.close()


def get_map():
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    sql = "select t.lid, t.fwd, t.rid, s.s_name, s.rank from TB_MAP t, tb_segment s where t.lid = s.s_id "
    cursor.execute(sql)
    road_map = {}
    reverse_list = defaultdict(list)
    for item in cursor:
        lid, fwd, rid, s_name, rank = item
        if rank != '高速公路' and rank != '快速路' and s_name != '320国道' and s_name != '02省道':
            road_map[rid] = s_name
            reverse_list[s_name].append(rid)
    cursor.close()
    conn.close()
    return road_map, reverse_list


def highway():
    tup_list = []
    conn = cx_Oracle.connect("hz/hz@192.168.11.88/orcl")
    cursor = conn.cursor()
    sql = "select t.lid, t.fwd, t.rid, s.s_name, s.rank from TB_MAP t, tb_segment s where t.lid = s.s_id "
    cursor.execute(sql)
    for item in cursor:
        lid, fwd, rid, s_name, rank = item
        if rank == '快速路':
            tup_list.append((s_name, rid))
    sql = "delete from tb_highway"
    cursor.execute(sql)
    sql = "insert into tb_highway values(:1, :2)"
    cursor.executemany(sql, tup_list)
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
