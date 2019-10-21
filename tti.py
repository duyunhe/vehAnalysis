# -*- coding: utf-8 -*-
# @Time    : 2019/6/18 17:27
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : tti.py


def get_tti_b0(speed):
    """
    beta 1.0 absolute speed
    tti in [0, 10]
    :return: 
    """
    if speed >= 60:
        return 10.0
    return speed / 6


def get_tti_v0(speed, def_speed):
    """
    :param speed: 路段实际速度
    :param def_speed: 路段期望速度
    :return: tti
    """
    if speed < 1e-5:
        speed = 0.1
    radio = def_speed / speed
    max_radio = 3.0
    min_radio = 1.0
    if radio >= max_radio:
        tti = 9.9
    elif radio <= min_radio:
        tti = 0
    else:
        tti = (radio - min_radio) / (max_radio - min_radio) * 10
    return tti
