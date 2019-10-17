# -*- coding: utf-8 -*-
# @Time    : 2019/10/16 17:45
# @Author  : 
# @简介    : 
# @File    : history_stat.py


from fetchData import get_gps_data, get_gps_list
from mapMatching0 import match_trace, static_road_speed
from collections import defaultdict
from time import clock
from map_info.readMap import MapInfo
import multiprocessing
from datetime import datetime, timedelta
from db.saveHisSpeed import save_speed


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "analysis.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


def match_process(trace_list, temp_speed):
    mi = MapInfo("../map_info/hz3.db")
    for trace in trace_list:
        match_trace(trace, mi, temp_speed)


@debug_time
def multi_main(bt):
    et = bt + timedelta(hours=1)
    trace_dict = get_gps_data(all_data=True, begin_time=bt, end_time=et)
    trace_list, cnt = get_gps_list(trace_dict)
    print len(trace_list), cnt
    if cnt == 0:
        return
    manager = multiprocessing.Manager()
    temp_speed = manager.dict()
    # 多进程支持
    thread_num = 16
    pool = multiprocessing.Pool(processes=thread_num)
    # bt = clock()
    for i in range(thread_num):
        pool.apply_async(match_process, args=(trace_list[i::thread_num], temp_speed))
    pool.close()
    pool.join()
    # et = clock()
    # print "multi", et - bt
    mi = MapInfo("../map_info/hz3.db")
    road_speed, cnt = static_road_speed(mi, temp_speed)
    save_speed(road_speed, bt)


def main():
    bt = datetime(2018, 5, 1)
    ft = datetime(2018, 6, 1)
    while bt < ft:
        bt0 = datetime(bt.year, bt.month, bt.day, 1)
        ft0 = bt0 + timedelta(hours=4)
        while bt0 < ft0:
            print bt0
            multi_main(bt0)
            bt0 += timedelta(hours=1)
        bt += timedelta(days=1)


def main1():
    bt = datetime(2018, 5, 5, 4)
    multi_main(bt)


if __name__ == '__main__':
    main1()
