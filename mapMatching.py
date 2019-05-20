# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 14:30
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : mapMatching.py

from time import clock


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "mm.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


def match_trace(trace, speed_list, trace_match):
    """
    :param trace: TaxiData
    :param speed_list: RoadSpeed(lid, ort, speed)
    :param trace_match: MatchRecord
    :return: 
    """
    if len(trace) == 0:
        return
    trace_match = []
