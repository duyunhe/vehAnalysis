# -*- coding: utf-8 -*-
# @Time    : 2019/5/27 18:39
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : taxiStruct.py

from datetime import datetime


class TaxiData:
    def __init__(self, veh="", px=0, py=0, stime=datetime(2019, 1, 1), state=0,
                 speed=0, car_state=0, direction=0):
        self.veh = veh
        self.x, self.y, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.car_state, self.direction = car_state, direction

    def __sub__(self, other):
        return (self.stime - other.stime).total_seconds()


def cmp_gps(data1, data2):
    if data1.stime > data2.stime:
        return 1
    elif data1.stime < data2.stime:
        return -1
    else:
        return 0
