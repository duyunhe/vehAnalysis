# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 16:09
# @Author  : yhdu@tongwoo.cn
# @简介    : 主程序集成，获取道路信息、GPS数据，统计计算并返回速度
# @File    : analysisGPS.py


from fetchRedis import get_gps_data, get_gps_list
from mapMatching0 import match_trace, static_road_speed
from collections import defaultdict
from time import clock
from map_info.readMap import MapInfo
import multiprocessing
from datetime import datetime


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "analysis.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


@debug_time
def main():
    trace_dict = get_gps_data()
    temp_speed = defaultdict(list)
    mi = MapInfo("./map_info/hz3.db")
    i = 0
    for veh, trace in trace_dict.iteritems():
        match_trace(trace, mi, temp_speed)
        i += 1
    road_speed, cnt = static_road_speed(mi, temp_speed)
    print len(road_speed)


def match_process(trace_list, temp_speed):
    mi = MapInfo("./map_info/hz3.db")
    for trace in trace_list:
        match_trace(trace, mi, temp_speed)


@debug_time
def multi_main():
    bt = clock()
    trace_dict = get_gps_data()
    trace_list, cnt = get_gps_list(trace_dict)
    print len(trace_list), cnt
    if cnt == 0:
        return
    et = clock()
    print et - bt

    manager = multiprocessing.Manager()
    temp_speed = manager.dict()

    pool = multiprocessing.Pool(processes=12)
    thread_num = 12
    bt = clock()
    for i in range(thread_num):
        pool.apply_async(match_process, args=(trace_list[i::thread_num], temp_speed))
    pool.close()
    pool.join()
    et = clock()
    print "multi", et - bt
    mi = MapInfo("./map_info/hz3.db")
    road_speed, cnt = static_road_speed(mi, temp_speed)
    print len(road_speed)


if __name__ == '__main__':
    multi_main()
