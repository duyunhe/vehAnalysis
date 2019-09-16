# -*- coding: utf-8 -*-
# @Time    : 2019/9/6 9:57
# @Author  : 
# @简介    : 
# @File    : mq_split.py


import stomp
import time
import logging
import os
import subprocess
import json
import struct
import redis
from datetime import datetime
from geo import in_hz, gcj02_to_wgs84
from coord import bl2xy
from collections import defaultdict
import cx_Oracle


veh_trace = defaultdict(list)
last_state = {}
confirm_state = {}
error_car = set()
INTERVAL_CNT = 10000
conn_redis = None
conn_mq = {}
cbid = None


def get_cbid():
    conn_db = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    cur = conn_db.cursor()
    sql = "select max(cbid) from tb_gps_trace"
    max_id = 0
    cur.execute(sql)
    for item in cur:
        max_id = item[0]
    cur.close()
    if max_id is None:
        max_id = 0
    conn_db.close()
    return max_id


def save_db(isu, cbid, state, data_list):
    conn = cx_Oracle.connect('hz_data/hz_data@192.168.11.88/orcl')
    tup_list = []
    for data in data_list:
        tup = (isu, data.px, data.py, data.speed_time, state, cbid)
        tup_list.append(tup)
    sql = "insert into tb_gps_trace (vhic, longi, lati, speed_time, state, cbid) values(:1, :2, :3, :4, :5, :6)"
    cur = conn.cursor()
    cur.executemany(sql, tup_list)
    conn.commit()

    sql = "insert into tb_area_trace (vhic, dep_longi, dep_lati, dest_longi, dest_lati, dep_time, dest_time, " \
          "state, cbid) values(:1, :2, :3, :4, :5, :6, :7, :8, :9)"
    tup = (isu, data_list[0].px, data_list[0].py, data_list[-1].px, data_list[-1].py, data_list[0].speed_time,
           data_list[-1].speed_time, state, cbid)
    cur.execute(sql, tup)
    conn.commit()
    cur.close()
    conn.close()


class TaxiData(object):
    def __init__(self, px, py, st):
        self.px, self.py, self.speed_time = px, py, st


def isu2str(msg):
    total_str = ""         # t打头，代表taxi
    for m in msg:
        # print ord(m)
        total_str += "{0:^02x}".format(ord(m))
    return total_str


def bcd2time(bcd_time):
    dig = []
    for bcd in bcd_time:
        a = (ord(bcd) & 0xF0) >> 4
        b = (ord(bcd) & 0x0F) >> 0
        dig.append(a * 10 + b)
    yy, mm, dd, hh, mi, ss = dig[0:6]
    try:
        dt = datetime(2000 + yy, mm, dd, hh, mi, ss)
    except ValueError:
        # print yy, mm, dd, hh, mi, ss
        return "", ""
    str_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
    return str_dt, dt


def get_car_state(state):
    """
    :param state: 车辆状态位
    :return: 卫星定位，empty or load
    """
    return (state >> 0) & 1, (state >> 9) & 1


def trans(src):
    message = ""
    L = len(src)
    i = 0
    while i < L:
        if i < len(src) - 1:
            if ord(src[i]) == 0x7d and ord(src[i + 1]) == 0x02:
                message += chr(0x7e)
                i += 2
            elif ord(src[i]) == 0x7d and ord(src[i + 1]) == 0x01:
                message += chr(0x7d)
                i += 2
            else:
                message += src[i]
                i += 1
        else:
            message += src[i]
            i += 1
    return message


class My905Listener(stomp.ConnectionListener):
    def __init__(self, gateway):
        self.gateway = gateway
        self.cnt = 0
        self.ticker = time.clock()

    def on_message(self, headers, message):
        message = trans(message)
        isu = message[5:11]
        body = message[13:32]
        stime = message[32:38]
        _, speed_time = bcd2time(stime)
        if speed_time == "":  # 异常
            return
        str_isu = isu2str(isu)
        # print str_isu
        alarm, state, lat, lng, spd, ort = struct.unpack("!IIIIHB", body)
        pos, load = get_car_state(state)
        # print lat, lng, spd
        wglat, wglng = float(lat) / 600000, float(lng) / 600000
        if in_hz(wglat, wglng):
            mlat, mlng = gcj02_to_wgs84(wglat, wglng)
            x, y = bl2xy(mlat, mlng)
            spd = float(spd) / 10
            # 用json字符串发送
            msg_key = self.gateway[0] + str(self.cnt % 10000000)
            # msg_dict = {'isu': str_isu, 'x': x, 'y': y, 'speed': spd,
            #             'speed_time': speed_time, 'pos': pos, 'load': load, 'ort': ort}
            veh_data = TaxiData(wglng, wglat, speed_time)
            try:
                ls = last_state[str_isu]
            except KeyError:
                ls = -1
            last_state[str_isu] = load
            if load == ls:
                try:
                    cs = confirm_state[str_isu]
                except KeyError:
                    cs = 0
                if cs == 1:
                    pass
                veh_trace[str_isu].append(veh_data)
                if len(veh_trace[str_isu]) > 5000:
                    print str_isu, "over"
            else:
                if 2 < len(veh_trace[str_isu]) < 500:
                    global cbid
                    save_db(str_isu, cbid, ls, veh_trace[str_isu])
                    cbid += 1
                veh_trace[str_isu] = [veh_data]

            self.cnt += 1
            if self.cnt % INTERVAL_CNT == 0:
                self.on_cnt(time.clock() - self.ticker)
                self.ticker = time.clock()

    def on_cnt(self, x):
        print "{1} net-gateway get {0} records cost ".format(INTERVAL_CNT, self.gateway), x, "seconds", datetime.now()

    def on_disconnected(self):
        print self.gateway, "disconnected"
        connect_mq()


def connect_and_subscribe(gateway):
    global conn_mq
    print 'ActiveMQ connecting...'
    try:
        c = conn_mq[gateway]
        if c is not None:
            try:
                c.stop()
            except Exception as e:
                print e, 'can not stop'
        listener = My905Listener(gateway)
        c = stomp.Connection10([('192.168.0.102', 61615)])
        c.set_listener('', listener)
        c.start()
        c.connect('admin', 'admin', wait=True)
        c.subscribe(destination='/topic/position_{0}'.format(gateway), ack='auto')
    except Exception as e:
        print e
        print 'ActiveMQ not connected!', datetime.now()
        print 'Reconnecting now...'
        time.sleep(15)
        connect_and_subscribe(gateway)
    print "topic {0} connected".format(gateway), datetime.now()


def connect_mq():
    global conn_mq
    gateways = ['ty', 'ft', 'hq']
    for g in gateways:
        connect_and_subscribe(g)


def check_network():
    fp = open(os.devnull, 'w')
    ret = subprocess.call('ping 192.168.0.102', shell=True, stdout=fp, stderr=fp)
    # print "check", ret
    if ret:
        connect_mq()
    fp.close()


if __name__ == '__main__':
    logging.basicConfig(filename='mq_test.txt', format="%(asctime)s %(message)s", level=logging.WARNING)
    # conn_redis = redis.Redis(host="192.168.11.229", port=6300, db=1)
    cbid = get_cbid()
    for g in ['ty', 'ft', 'hq']:
        conn_mq[g] = None
    connect_mq()
    while True:
        time.sleep(30)
        check_network()
