# -*- coding: utf-8 -*-
# @Time    : 2019/11/14 18:22
# @Author  : yhdu@tongwoo.cn
# @简介    : Bus Station Travel Time
# @File    : BSTT.py

from datetime import datetime, timedelta
from mapMatching import match_path
from taxiStruct import TaxiData
from map_info.readMap import MapInfo
from geo import calc_dist
from coord import bl2xy
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
from route import get_route, get_route1, save_route_road, delete_route_road


def get_stop_list():
    fp = open('route.txt')
    items = []
    for line in fp.readlines():
        items = line.strip('\n').split(';')
    stop_list = []
    for item in items:
        l, b = map(float, item.split(','))
        x, y = bl2xy(b, l)
        stop_list.append((x, y))
    return stop_list


def trace_passby(trace, pos0, pos1):
    """
    :param trace: list[TaxiData]
    :param pos0: (x, y) 
    :param pos1: (x, y)
    :return: 
    """
    bi, ei = None, None
    for i, data in enumerate(trace):
        pos = data.x, data.y
        if calc_dist(pos, pos0) < 1000:
            bi = i
        if calc_dist(pos, pos1) < 1000:
            ei = i
    if bi is not None and ei is not None:
        print trace[0].veh, trace[bi].stime, trace[ei].stime
    return


def draw_line(line, mark=False):
    x_list, y_list = [], []
    for pt in line.point_list:
        x, y = pt.x, pt.y
        x_list.append(x)
        y_list.append(y)
    if not mark:
        plt.plot(x_list, y_list, color='k')
    else:
        plt.plot(x_list, y_list, color='b', linewidth=2)
        x, y = np.mean(x_list), np.mean(y_list)
        plt.text(x, y, str(line.lid))


def draw_stop(stop_list):
    x_list, y_list = zip(*stop_list)
    plt.plot(x_list, y_list, marker='o', markersize=5, linestyle='')
    for i, xy in enumerate(stop_list):
        x, y = xy
        plt.text(x, y, str(i))


def draw_route(pt_list):
    x_list, y_list = zip(*pt_list)
    plt.plot(x_list, y_list, color='b')


def match_stop(name, stop_list, mi):
    taxi_list = [TaxiData(px=stop[0], py=stop[1]) for stop in stop_list]
    trace_match = match_path(taxi_list, mi)
    path_list = []
    tup_list = []
    last_stop = None
    lid_set = set()
    for i, match in enumerate(trace_match):
        if i > 0:
            try:
                path = match.best_trans.pt_path
                lps = match.best_trans.line_path
                dist_dict = defaultdict(int)
                for lp in lps:
                    ln = (lp.line.lid, lp.forward)
                    lid_set.add(lp.line.lid)
                    dist_dict[ln] += lp.dist
                for ln, dist in dist_dict.items():
                    tup = (name, i, dist, ln[0], int(ln[1]))
                    tup_list.append(tup)
                path_list.append(path)
            except AttributeError:
                dist = calc_dist([taxi_list[i].x, taxi_list[i].y], [last_stop.x, last_stop.y])
                tup = (name, i, dist, -1, 0)
                tup_list.append(tup)
                print i
        last_stop = taxi_list[i]
    save_route_road(tup_list)
    # for path in path_list:
    #     route = [(pt.x, pt.y) for pt in path]
    #     draw_route(route)
    return lid_set


def main():
    delete_route_road()
    mi = MapInfo('../map_info/hz3.db')
    # stop_list = get_stop_list()
    stop_list = None
    route_dict = get_route()
    i = 0
    for name, route in route_dict.items():
        print i, name
        # if i != 4:
        #     i += 1
        #     continue
        stop_list = route
        # draw_stop(stop_list)
        rid_set = match_stop(name, stop_list, mi)
        # for line in mi.line_list:
        #     if line.lid in rid_set:
        #         draw_line(line, mark=True)
        #     else:
        #         draw_line(line)
        i += 1
    # plt.show()


if __name__ == "__main__":
    main()
