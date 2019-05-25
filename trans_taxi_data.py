# -*- coding: utf-8 -*-
# @Time    : 2019/5/16 17:55
# @Author  : yhdu@tongwoo.cn
# @简介    : 获取taxi数据源,ETL成json并转发至redis
# @File    : trans_taxi_data.py

import stomp
import time
import logging
import os
import subprocess
import json
import struct
import redis
from datetime import datetime
from geo import bl2xy, in_hz, gcj02_to_wgs84

# 84 to 02
a = 6378245.0
ee = 0.00669342162296594323
# World Geodetic System ==> Mars Geodetic System

INTERVAL_CNT = 10000
conn_redis = None


def isu2str(msg):
    total_str = "t"         # t打头，代表taxi
    for m in msg:
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
        return ""
    str_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
    return str_dt


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
        speed_time = bcd2time(stime)
        if speed_time == "":  # 异常
            return
        str_isu = isu2str(isu)
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
            msg_dict = {'isu': str_isu, 'x': x, 'y': y, 'speed': spd,
                        'speed_time': speed_time, 'pos': pos, 'load': load, 'ort': ort}
            try:
                msg_json = json.dumps(msg_dict)
            except UnicodeDecodeError:
                # print msg_dict
                return
            # global conn_redis
            # conn_redis.set(name=msg_key, value=msg_json, ex=600)
            self.cnt += 1
            if self.cnt % INTERVAL_CNT == 0:
                self.on_cnt(time.clock() - self.ticker)
                self.ticker = time.clock()

    def on_cnt(self, x):
        print "{1} net-gateway get {0} records cost ".format(INTERVAL_CNT, self.gateway), x, "seconds", datetime.now()

    def on_disconnected(self):
        print self.gateway, "disconnected"
        connect_and_subscribe(self.gateway)


def connect_and_subscribe(gateway):
    print 'ActiveMQ connecting...'
    try:
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
    conn_redis = redis.Redis(host="192.168.11.229", port=6300, db=1)
    connect_mq()
    while True:
        time.sleep(30)
        check_network()
