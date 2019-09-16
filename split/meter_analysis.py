# -*- coding: utf-8 -*-
# @Time    : 2019/9/9 15:39
# @Author  : 
# @简介    : 
# @File    : meter_analysis.py


import cx_Oracle
from collections import defaultdict
from datetime import datetime, timedelta
from math import fabs
from time import clock


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "fetch.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


class MeterData(object):
    def __init__(self, zx, dep_time, dest_time, dist, ks):
        self.zx, self.dep_time, self.dest_time, self.dist, self.ks = zx, \
        dep_time, dest_time, dist, ks

    def __lt__(self, other):
        if self.dep_time == other.dep_time:
            return self.dest_time < other.dest_time
        return self.dep_time < other.dep_time

    def __sub__(self, other):
        """
        :param other: TraceData 
        :return: 
        """
        return (self.dep_time - other.dep_time).total_seconds(), (self.dest_time - other.dest_time).total_seconds()


class TraceData(object):
    def __init__(self, dep_time, dest_time, cbid):
        self.dep_time, self.dest_time, self.cbid = dep_time, dest_time, cbid

    def __sub__(self, other):
        """
        :param other: MeterData 
        :return: 
        """
        return (self.dep_time - other.dep_time).total_seconds(), (self.dest_time - other.dest_time).total_seconds()


@debug_time
def get_offset(bt):
    off_dict = {}
    td = datetime(bt.year, bt.month, bt.day)
    conn = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    cur = conn.cursor()
    sql = "select vhic, predict_off_time from tb_offset_predict where db_time = :1"
    tup = (td, )
    cur.execute(sql, tup)
    for item in cur:
        veh, off_time = item[:]
        off_dict[veh] = off_time
    cur.close()
    conn.close()
    return off_dict


@debug_time
def get_meter_data(bt, et):
    conn = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    cur = conn.cursor()
    y, m = bt.year, bt.month
    table_name = "hz.jjq{0}{1:02d}_1".format(y, m)
    sql = "select cphm_new, zhongxin, shangche, xiache, jicheng, kongshi from {0} where zhongxin >= :1 " \
          "and zhongxin < :2 " \
          "order by zhongxin".format(table_name)
    tup = (bt, et)
    cur.execute(sql, tup)
    cur_dict = defaultdict(list)
    cnt = 0
    for item in cur:
        veh, zx, sc, xc, jc, ks = item[:]
        cnt += 1
        try:
            jc = float(jc) / 10
        except ValueError:
            print "jc error", jc
            continue
        try:
            ks = float(ks) / 10
        except ValueError:
            print "ks error", ks
            continue
        m_data = MeterData(zx, sc, xc, jc, ks)
        cur_dict[veh].append(m_data)
    cur.close()
    conn.close()
    print "meter origin", cnt
    for veh, m_list in cur_dict.items():
        m_list.sort()
        cur_dict[veh] = m_list
    return cur_dict


def get_trace(bt, et):
    # 扩大范围，减小服务器时间误差带来的影响
    bt = bt - timedelta(minutes=5)
    conn = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    cur = conn.cursor()
    sql = "select vhic, dep_time, dest_time, cbid from tb_area_trace where dest_time >= :1 and dest_time < :2 " \
          "and state = '1' order by dep_time"
    tup = (bt, et)
    cur.execute(sql, tup)
    trace_dict = {}
    trace_cnt = 0
    for item in cur:
        trace_cnt += 1
        vhic, dep_time, dest_time, cbid = item[:]
        vhic = vhic[3:]
        t_data = TraceData(dep_time, dest_time, cbid)
        try:
            trace_dict[vhic].append(t_data)
        except KeyError:
            trace_dict[vhic] = [t_data]
    cur.close()
    conn.close()
    print "trace origin", trace_cnt
    return trace_dict


def time_around(dt, dft, off_time):
    return fabs((dt - dft).total_seconds()) < off_time * 60


def get_match_tup(m_data, trace):
    cbid = trace.cbid
    dist, ks = m_data.dist, m_data.ks
    return cbid, dist, ks


def order_match(veh, m_list, off_time, trace_list):
    len_m, len_t = len(m_list), len(trace_list)
    tup_list = []
    del_list = []
    i, j = 0, 0
    while i < len_m and j < len_t:
        m_data, trace = m_list[i], trace_list[j]
        dt, at = m_data.dep_time + timedelta(minutes=off_time), m_data.dest_time + timedelta(minutes=off_time)
        if time_around(dt, trace.dep_time, 5) and time_around(at, trace.dest_time, 5):
            i, j = i + 1, j + 1
            tup = get_match_tup(m_data, trace)
            tup_list.append(tup)
        else:
            if dt < trace.dep_time:
                i = i + 1
            else:
                if j > 0:
                    del_list.append(trace.cbid)
                j = j + 1
    return tup_list, del_list


def order_match_v1(veh, m_list, trace_list):
    """
    without off_time
    :param veh: 
    :param m_list: 
    :param trace_list: 
    :return: tup_list: list of tup(cbid, jc, ks), del_list: list of cbid
    """
    len_m, len_t = len(m_list), len(trace_list)
    tup_list = []
    del_list = []
    off_set = set()
    match_tup = []
    for i in range(len_m):
        for j in range(len_t):
            off_dep, off_dest = trace_list[j] - m_list[i]
            if fabs(off_dep - off_dest) < 90:
                off = (off_dep + off_dest) / 2
                off_set.add(off)
                match_tup.append((i, j, off))
    def_off, off_cnt = 0, 0
    match_record = []
    for off in off_set:
        cnt = 0
        rec = []
        for tup in match_tup:
            i, j, t_off = tup[:]
            if fabs(off - t_off) < 60:
                cnt += 1
                rec.append((i, j))
        if cnt > off_cnt:
            def_off, off_cnt = off, cnt
            match_record = rec

    for rec in match_record:
        i, j = rec[:]
        tup = get_match_tup(m_list[i], trace_list[j])
        tup_list.append(tup)
    return tup_list, del_list


def update_order(conn, upd_list, del_list):
    sql = "update tb_area_trace set dist = :1, empty_dist = :2 where cbid = :3"
    tup_list = []
    for tup in upd_list:
        cbid, dist, ks = tup[:]
        tup_list.append((dist, ks, cbid))
    for cbid in del_list:
        tup_list.append((-2, 0, cbid))
    cur = conn.cursor()
    cur.executemany(sql, tup_list)
    cur.close()


def match(meter_dict, off_dict, trace_dict):
    match_cnt, meter_cnt, del_cnt = 0, 0, 0
    no_trace_cnt = 0
    no_off_cnt = 0
    conn = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    for veh, m_list in meter_dict.items():
        if veh != 'AT3692':
            continue
        try:
            off_time = off_dict[veh]
        except KeyError:
            no_off_cnt += len(m_list)
            # print veh, "no off time"
            try:
                trace_list = trace_dict[veh]
            except KeyError:
                no_trace_cnt += len(m_list)
                # print veh, "no trace list"
                continue
            tup_list, del_list = order_match_v1(veh, m_list, trace_list)
            match_cnt += len(tup_list)
            del_cnt += len(del_list)
            continue
        try:
            trace_list = trace_dict[veh]
        except KeyError:
            no_trace_cnt += len(m_list)
            # print veh, "no trace list"
            continue
        meter_cnt += len(m_list)
        # tup_list, del_list = order_match(veh, m_list, off_time, trace_list)
        tup_list, del_list = order_match_v1(veh, m_list, trace_list)
        update_order(conn, tup_list, del_list)
        match_cnt += len(tup_list)
        del_cnt += len(del_list)

    conn.commit()
    conn.close()
    print match_cnt, meter_cnt, no_trace_cnt, no_off_cnt, del_cnt


def proc():
    bt = datetime(2018, 5, 1, 14, 0)
    et = datetime(2018, 5, 1, 15, 0)
    meter_dict = get_meter_data(bt, et)
    off_dict = get_offset(bt)
    trace_dict = get_trace(bt, et)
    match(meter_dict, off_dict, trace_dict)


if __name__ == '__main__':
    proc()
