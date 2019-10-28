# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 16:09
# @Author  : yhdu@tongwoo.cn
# @简介    : 主程序集成，获取道路信息、GPS数据，统计计算并返回速度
# @File    : analysisGPS.py


from fetchData import get_formal_data, get_gps_list, get_def_speed
from mapMatching0 import match_trace, static_road_speed
from collections import defaultdict
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
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
def multi_main(history):
    """
    该函数在5分钟内将调用两次，一次是五分钟整，一次是2分半
    :param history: 整五分钟的计算需要记录到历史数据库，反之不需要记录 
    :return: 
    """
    run_time = datetime.now()
    dt = run_time - timedelta(minutes=1)
    print "****** main ******", run_time
    bt = dt - timedelta(minutes=6)
    trace_dict, on_time_dict = get_formal_data(all_data=True, begin_time=bt, end_time=dt)
    trace_list, cnt = get_gps_list(trace_dict)
    print "multi main", len(trace_list), cnt

    manager = multiprocessing.Manager()
    temp_speed = manager.list()
    # 多进程支持
    thread_num = 16
    pool = multiprocessing.Pool(processes=thread_num)
    for i in range(thread_num):
        pool.apply_async(match_process, args=(trace_list[i::thread_num], temp_speed))
    pool.close()
    pool.join()
    mi = MapInfo("./map_info/hz3.db")
    road_speed, cnt_dict = static_road_speed(mi, temp_speed)
    def_speed = get_def_speed()
    save_tti(road_speed, cnt_dict, def_speed, run_time, history)


if __name__ == '__main__':
    logging.basicConfig()
    scheduler = BlockingScheduler()
    with_history = {"history": True}
    without_history = {"history": False}
    scheduler.add_job(func=multi_main, trigger='cron', kwargs=with_history,
                      minute='*/5', max_instances=10)
    scheduler.add_job(func=multi_main, trigger='cron', kwargs=without_history,
                      minute='2-58/5', second='30', max_instances=10)
    scheduler.start()
