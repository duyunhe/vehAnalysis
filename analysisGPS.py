# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 16:09
# @Author  : yhdu@tongwoo.cn
# @简介    : 主程序集成，获取道路信息、GPS数据，统计计算并返回速度
# @File    : analysisGPS.py


from fetchData import get_formal_data, get_gps_list, get_def_speed
from mapMatching0 import match_trace, static_road_speed
from collections import defaultdict
from time import clock
from map_info.readMap import MapInfo
import multiprocessing
from db.saveHisSpeed import save_speed, save_tti
from datetime import datetime, timedelta


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
        match_trace(trace, mi, temp_speed)


@debug_time
def multi_main():
    dt = datetime.now() - timedelta(minutes=2)
    bt = dt - timedelta(minutes=7)
    trace_dict = get_formal_data(all_data=True, begin_time=bt, end_time=dt)
    trace_list, cnt = get_gps_list(trace_dict)
    print "multi main", len(trace_list), cnt

    manager = multiprocessing.Manager()
    temp_speed = manager.list()
    # 多进程支持
    thread_num = 4
    pool = multiprocessing.Pool(processes=thread_num)
    bt = clock()
    for i in range(thread_num):
        pool.apply_async(match_process, args=(trace_list[i::thread_num], temp_speed))
    pool.close()
    pool.join()
    et = clock()
    print "multi", et - bt
    mi = MapInfo("./map_info/hz3.db")
    road_speed, cnt_dict = static_road_speed(mi, temp_speed)
    def_speed = get_def_speed()
    save_tti(road_speed, cnt_dict, mi, def_speed, dt)


if __name__ == '__main__':
    multi_main()
