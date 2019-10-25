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
from db.saveHisSpeed import save_speed, truncate_table


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
def multi_main(bt, all_data=True):
    et = bt + timedelta(hours=2)
    trace_dict = get_gps_data(all_data=all_data, begin_time=bt, end_time=et)
    trace_list, cnt = get_gps_list(trace_dict, history=True)
    print len(trace_list), cnt
    if cnt == 0:
        return
    manager = multiprocessing.Manager()
    temp_speed = manager.list()
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
    save_speed(road_speed, bt, cnt)


def main():
    truncate_table()
    bt = datetime(2018, 5, 1)
    ft = datetime(2018, 6, 1)
    while bt < ft:
        bt0 = datetime(bt.year, bt.month, bt.day, 1)
        ft0 = bt0 + timedelta(hours=4)
        while bt0 < ft0:
            print bt0
            multi_main(bt0)
            bt0 += timedelta(hours=2)
        bt += timedelta(days=1)


def main1():
    truncate_table()
    bt = datetime(2018, 5, 1, 1)
    multi_main(bt, True)


if __name__ == '__main__':
    main()
