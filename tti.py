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
