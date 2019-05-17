# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 16:40
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : readMap.py


import sqlite3
from map_struct import MapPoint


map_uid = {}        # assist for store string id, as map_uid["84354.12,92431.94"] = map_point
pt_cnt = 0          # global pid, as current counter


def insert_map_point(pt, mp_list):
    """
    :param pt: MapPoint
    :param mp_list: list of MapPoint, each assign one pid
    :return: pid
    """
    global map_uid, pt_cnt
    str_pt = str(pt)
    try:
        pt = map_uid[str_pt]
    except KeyError:
        pt.pid = pt_cnt
        map_uid[str_pt] = pt
        pt_cnt += 1
        mp_list.append(pt)
    return pt.pid


def read_sqlite():
    conn = sqlite3.connect("hz3.db")
    cur = conn.cursor()
    sql = "select s_id, seq, px, py from tb_seg_point order by s_id, seq"
    cur.execute(sql)
    point_list = []
    line_list = []
    for item in cur:
        sid, seq, x, y = item[:]
        mp = MapPoint(x, y)
        insert_map_point(mp, point_list)
    cur.close()
    conn.close()


read_sqlite()
