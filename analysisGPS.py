# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 16:09
# @Author  : yhdu@tongwoo.cn
# @简介    : 主程序集成，获取道路信息、GPS数据，统计计算并返回速度
# @File    : analysisGPS.py


from fetchData import get_gps_data, get_gps_list
from mapMatching0 import match_trace, static_road_speed
from collections import defaultdict
from time import clock
from map_info.readMap import MapInfo
import multiprocessing
from db.saveHisSpeed import save_speed
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
    trace_dict = get_gps_data(all_data=False)
    trace_list, cnt = get_gps_list(trace_dict)
    print len(trace_list), cnt
    if cnt == 0:
        return

    manager = multiprocessing.Manager()
    temp_speed = manager.dict()
    # 多进程支持
    thread_num = 1
    pool = multiprocessing.Pool(processes=thread_num)
    bt = clock()
    for i in range(thread_num):
        pool.apply_async(match_process, args=(trace_list[i::thread_num], temp_speed))
    pool.close()
    pool.join()
    et = clock()
    print "multi", et - bt
    mi = MapInfo("./map_info/hz3.db")
    road_speed, cnt = static_road_speed(mi, temp_speed)
    save_speed(road_speed, datetime.now())
    for line, spd in road_speed.items():
        if spd < 5:
            print line, spd


if __name__ == '__main__':
    multi_main()
