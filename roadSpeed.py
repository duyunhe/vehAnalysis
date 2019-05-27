# -*- coding: utf-8 -*-
# @Time    : 2019/5/27 16:00
# @Author  : yhdu@tongwoo.cn
# @简介    : 操作数据库
# @File    : roadSpeed.py


import cx_Oracle
from time import clock
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "roadSpeed.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


