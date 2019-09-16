# -*- coding: utf-8 -*-
# @Time    : 2019/5/28 15:43
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : historySpeed.py


import multiprocessing
from fetchData import get_gps_data, get_gps_list
import mapMatching0
from datetime import datetime, timedelta
from db.saveHisSpeed import save_speed
from collections import defaultdict
from time import clock
from map_info.readMap import MapInfo


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "analysis.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


def match_process(trace_list, temp_speed):
    mi = MapInfo("./map_info/hz3.db")
    for trace in trace_list:
        mapMatching0.match_trace(trace, mi, temp_speed)


@debug_time
def stat_day(bt, et):
    # mi = MapInfo("./map_info/hz3.db")
    trace_dict = get_gps_data(True, bt, et)
    trace_list, pt_cnt = get_gps_list(trace_dict)
    print len(trace_list), pt_cnt
    # manager = multiprocessing.Manager()
    # temp_speed = manager.dict()
    # pool = multiprocessing.Pool(processes=2)
    # thread_num = 2
    bt = clock()
    temp_speed = defaultdict(list)
    match_process(trace_list, temp_speed)
    # for i in range(thread_num):
    #     pool.apply_async(match_process, args=(trace_list[i::thread_num], temp_speed))
    # pool.close()
    # pool.join()
    et = clock()
    print "stat one day", et - bt
    # temp_speed = defaultdict(list)
    # pt_cnt = 0
    # for trace in trace_list:
    #     pt_cnt += len(trace)
    #     # if pt_cnt > 10000:
    #     #     break
    #     mapMatching0.match_trace(trace, mi, temp_speed)
    save_speed(temp_speed)
    # road_speed, cnt = mapMatching0.static_road_speed(mi, temp_speed)
    # print cnt
    # print len(road_speed)
    # for road in sorted(road_speed.keys()):
    #     print road, road_speed[road]


def main():
    bt = datetime(2017, 11, 1, 1)
    ft = datetime(2017, 12, 1)
    while bt < ft:
        print bt
        et = bt + timedelta(hours=4)
        stat_day(bt, et)
        bt += timedelta(days=1)


if __name__ == '__main__':
    main()
