# -*- coding: utf-8 -*-
# @Time    : 2019/9/11 16:59
# @Author  : 
# @简介    : 匹配
# @File    : trace_m.py

from math import fabs
from datetime import datetime, timedelta


class Trace(object):
    def __init__(self, trace, dist, ks, state):
        self.trace, self.dist, self.ks, self.state = trace, dist, ks, state


def split_trace(data_list):
    last_state = -1
    trace, trace_list = [], []
    for i, data in enumerate(data_list):
        if data.state == last_state:
            trace[1] = i
        else:
            if last_state == 1:
                trace_list.append(trace)
            trace = [i, i]
        last_state = data.state
    if last_state == 1:
        trace_list.append(trace)
    return trace_list


def time_around(dt, dft, off_time):
    """
    :param dt: t0
    :param dft: t1
    :param off_time: minutes
    :return: 
    """
    return fabs((dt - dft).total_seconds()) < off_time * 60


def trace_split_off(meter_list, trace, off_time):
    """
    with offset time
    :param meter_list: 
    :param trace: 
    :param off_time: 
    :return: list of trace 
    """
    idx_list = split_trace(trace)
    i, j = 0, 0
    match_dict = {}
    m_len, i_len = len(meter_list), len(idx_list)

    vis_list = [0] * m_len      # matched first time
    while i < m_len and j < i_len:
        bi, ei = idx_list[j]
        m_data = meter_list[i]
        tbt, tet = trace[bi].speed_time, trace[ei].speed_time
        mbt, met = m_data.dep_time + timedelta(minutes=off_time), m_data.dest_time + timedelta(minutes=off_time)
        if time_around(tbt, mbt, 3) and time_around(tet, met, 3):
            tup = (m_data.dist, m_data.ks, bi, ei)
            vis_list[i] = 1
            match_dict[i] = tup
            i, j = i + 1, j + 1
        else:
            if tbt < mbt:
                j += 1
            else:
                i += 1
    # check ag. as much as possible
    pos = 0
    t_len = len(trace)
    for i in range(m_len):
        if vis_list[i]:
            continue
        # unvisited
        bi, ei = None, None
        mbt, met = meter_list[i].dep_time + timedelta(minutes=off_time), \
                   meter_list[i].dest_time + timedelta(minutes=off_time)
        while pos < t_len:
            tbt = trace[pos].speed_time
            if time_around(tbt, mbt, 1):
                if trace[pos].state == 1:
                    bi = pos
                    pos += 1
                    break
                else:
                    bi = pos
            pos += 1

        while pos < t_len:
            tet = trace[pos].speed_time
            if time_around(tet, met, 1):
                if trace[pos].state == 0:
                    ei = pos
                    pos += 1
                    break
                else:
                    ei = pos
            pos += 1

        if bi is not None and ei is not None:   # found
            tup = (meter_list[i].dist, meter_list[i].ks, bi, ei)
            match_dict[i] = tup
            vis_list[i] = 1

    trace_list = []
    li = -1
    for i in range(m_len):
        if vis_list[i]:
            tup = match_dict[i]
            dist, ks, bi, ei = tup[:]
            bi0, ei0 = li + 1, bi - 1
            if ei0 > bi0:
                t = trace[bi0:ei0 + 1]
                t_data = Trace(t, -1, -1, 0)
                trace_list.append(t_data)
            t = trace[bi: ei + 1]
            t_data = Trace(t, dist, ks, 1)
            trace_list.append(t_data)
            li = ei
    if t_len > li:
        t = trace[li + 1:t_len]
        t_data = Trace(t, -1, -1, 0)
        trace_list.append(t_data)
    else:
        print "here"
    return trace_list


def trace_split_no(meter_list, trace):
    """
    without any pre-information
    :param meter_list: 
    :param trace: 
    :return: 
    """