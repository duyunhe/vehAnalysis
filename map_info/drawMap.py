# -*- coding: utf-8 -*-
# @Time    : 2019/6/18 10:50
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : drawMap.py


import matplotlib.pyplot as plt
import sqlite3
from map_struct import MapSegment, MapPoint
from tti import get_tti_b0
from datetime import datetime, timedelta
from fetchData import get_gps_data, get_gps_list


def draw_line_idx(segment, idx):
    pt0 = segment.point_list[0]
    pt1 = segment.point_list[-1]
    plt.text((pt0.x + pt1.x) / 2, (pt0.y + pt1.y) / 2, str(idx))


def load_map():
    seg_list = []
    conn = sqlite3.connect("E:/job/vehanalysis/map_info/hz3.db")
    cur = conn.cursor()
    sql = "select s_id, seq, px, py from tb_seg_point order by s_id, seq"
    cur.execute(sql)
    last_id = -1
    for item in cur:
        lid, seq, px, py = item[:]
        mp = MapPoint(x=px, y=py)
        if last_id == lid:
            seg_list[lid].add_point(mp)
        else:
            seg = MapSegment(lid)
            seg.add_point(mp)
            seg_list.append(seg)
        last_id = lid
    cur.close()
    conn.close()
    return seg_list


def load_gene():
    point_list, seg_list = [], []
    conn = sqlite3.connect("E:/job/vehanalysis/map_info/hz1.db")
    cur = conn.cursor()
    sql = "select * from tb_map_point"
    cur.execute(sql)
    for item in cur:
        pid, x, y = item[:]
        mp = MapPoint(x, y)
        point_list.append(mp)
    sql = "select * from tb_gene_line_point order by line_id, seq"
    cur.execute(sql)
    last_id = -1
    for item in cur:
        lid, seq, pid = item[:]
        if last_id == lid:
            seg_list[lid].add_point(point_list[pid])
        else:
            seg = MapSegment(lid)
            seg.add_point(point_list[pid])
            seg_list.append(seg)
        last_id = lid
    sql = "select * from tb_gene_line"
    cur.execute(sql)
    seg_dict = {}
    for item in cur:
        sid, lid, ort, _ = item[:]
        uid = sid * 2 + int(ort)
        seg_dict[uid] = seg_list[sid]
    cur.close()
    conn.close()
    return seg_dict


def draw_seg(segment, c='k'):
    x_list, y_list = [], []
    for pt in segment.point_list:
        x_list.append(pt.x)
        y_list.append(pt.y)
    plt.plot(x_list, y_list, c=c)


def tti_color(tti):
    if tti < 2:
        return 'r'
    elif tti < 4:
        return 'gold'
    elif tti < 6:
        return 'y'
    elif tti < 8:
        return 'lime'
    else:
        return 'g'


def draw_road(seg_list, road_state=None):
    for line in seg_list:
        draw_seg(line)
        if line.lid == 4858:
            draw_line_idx(line, line.lid)


def draw_gps(gps_dict):
    # 实际上只有一辆车
    trace_list, cnt = get_gps_list(gps_dict)
    for gps_list in trace_list:
        xy_list = [[data.x, data.y] for data in gps_list]
        x_list, y_list = zip(*xy_list)
        plt.plot(x_list, y_list, marker='+', linestyle='', color='r')
        for i, data in enumerate(xy_list):
            plt.text(x_list[i] + 1, y_list[i] + 1, str(i))


def main():
    seg_list = load_map()
    draw_road(seg_list)
    dt = datetime(2018, 5, 1, 1)
    gps_dict = get_gps_data(all_data=False, begin_time=dt, end_time=dt + timedelta(hours=1))
    draw_gps(gps_dict)
    plt.show()


def draw_state(road_speed):
    road_state = {}
    for ln, speed in road_speed.items():
        lid, fwd = ln.lid, ln.fwd
        uid = lid * 2 + int(fwd)
        road_state[uid] = get_tti_b0(speed)
    seg_dict = load_gene()
    draw_road(seg_dict, road_state)


if __name__ == '__main__':
    main()
