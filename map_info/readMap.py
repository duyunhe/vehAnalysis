# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 16:40
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : readMap.py


import sqlite3
from map_struct import MapPoint, MapSegment, LinkDesc
from sklearn.neighbors import KDTree
import numpy as np
from time import clock
import random


map_uid = {}        # assist for store string id, as map_uid["84354.12,92431.94"] = map_point
pt_cnt = 0          # global pid, as current counter
ORT_ONEWAY = 1
ORT_DBWAY = 0


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "read map.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


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


def read_sqlite(filename):
    """
    read map, return line list (MapSegment) and point list (MapPoint)
    :param: filename db path & name
    :return: 
    """
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    sql = "select s_id, seq, px, py from tb_seg_point order by s_id, seq"
    cur.execute(sql)
    point_list, line_list = [], []
    last_sid = -1
    for item in cur:
        sid, seq, x, y = item[:]
        mp = MapPoint(x, y)
        pid = insert_map_point(mp, point_list)
        if sid != last_sid:
            ms = MapSegment(sid)
            line_list.append(ms)
        line_list[-1].add_point(point_list[pid])
        last_sid = sid

    sql = "select * from tb_segment"
    cur.execute(sql)
    for item in cur:
        sid, name, ort, rank, _, _ = item[:]
        ort = int(ort)
        line_list[sid].name = name
        line_list[sid].ort = ort
        line_list[sid].rank = rank

    for line in line_list:
        pt_len = len(line.point_list)

        for i, pt in enumerate(line.point_list):
            if line.ort == ORT_ONEWAY:
                ld = LinkDesc(line, i, True)
                rld = LinkDesc(line, i, False)
                if i < pt_len - 1:
                    line.point_list[i].add_link(ld, line.point_list[i + 1])
                    line.point_list[i + 1].add_rlink(rld, line.point_list[i])
            else:
                if i >= 1:
                    ld = LinkDesc(line, i - 1, False)
                    line.point_list[i].add_link(ld, line.point_list[i - 1])
                if i < pt_len - 1:
                    ld = LinkDesc(line, i, True)
                    line.point_list[i].add_link(ld, line.point_list[i + 1])

    cur.close()
    conn.close()
    return line_list, point_list


def make_kdtree(point_list):
    nd_list, id_list = [], []
    for i, pt in enumerate(point_list):
        id_list.append(i)
        nd_list.append([pt.x, pt.y])
    X = np.array(nd_list)
    return KDTree(X, leaf_size=2, metric="euclidean"), X


class MapInfo(object):
    def __init__(self, db_name="hz3.db"):
        self.line_list, self.point_list = read_sqlite(db_name)
        self.kdt, self.x = make_kdtree(self.point_list)


@debug_time
def query(mi):
    xy_list = []
    for i in range(100000):
        x, y = random.uniform(80000, 100000), random.uniform(80000, 100000)
        xy_list.append([x, y])
    idx, dst = mi.kdt.query(xy_list, k=20)
    flag = 0


def t():
    mi = MapInfo()
    query(mi)


