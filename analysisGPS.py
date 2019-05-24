# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 16:09
# @Author  : yhdu@tongwoo.cn
# @简介    : 主程序集成，获取道路信息、GPS数据，统计计算并返回速度
# @File    : analysisGPS.py

from fetchData import get_gps_data
from map_info.readMap import MapInfo
from mapMatching import match_trace


def main():
    trace_dict = get_gps_data()
    mi = MapInfo("./map_info/hz3.db")
    for veh, trace in trace_dict.iteritems():
        match_trace(trace, mi)


if __name__ == '__main__':
    main()
