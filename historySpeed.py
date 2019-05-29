# -*- coding: utf-8 -*-
# @Time    : 2019/5/28 15:43
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : historySpeed.py


from fetchRedis import get_gps_data, get_gps_list
from mapMatching0 import match_trace, static_road_speed
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
    pt_cnt = 0
    for trace in trace_list:
        pt_cnt += len(trace)
        match_trace(trace, mi, temp_speed)
        if pt_cnt > 10000:
            break


@debug_time
def main():
    mi = MapInfo("./map_info/hz3.db")
    trace_dict = get_gps_data()
    trace_list = get_gps_list(trace_dict)
    # print len(trace_list)
    temp_speed = defaultdict(list)
    pt_cnt = 0
    bt = clock()
    for trace in trace_list:
        pt_cnt += len(trace)
        # print len(trace)
        match_trace(trace, mi, temp_speed)
        if pt_cnt > 50000:
            break
    et = clock()
    print pt_cnt, et - bt
    # road_speed = static_road_speed(temp_speed)
    # print len(road_speed)
    # for road in sorted(road_speed.keys()):
    #     print road, road_speed[road]


if __name__ == '__main__':
    main()
