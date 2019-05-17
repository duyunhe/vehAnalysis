# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 16:12
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : fetchData.py


import cx_Oracle
from datetime import timedelta, datetime
from geo import bl2xy, calc_dist


class TaxiData:
    def __init__(self, veh, px, py, stime, state, speed, car_state, direction):
        self.veh = veh
        self.px, self.py, self.stime, self.state, self.speed = px, py, stime, state, speed
        self.car_state, self.direction = car_state, direction


def get_gps_data():
    end_time = datetime(2018, 5, 8, 15, 0, 0)
    conn = cx_Oracle.connect('hz/hz@192.168.11.88:1521/orcl')
    begin_time = end_time + timedelta(minutes=-10)
    sql = "select px, py, speed_time, state, speed, carstate, direction, vehicle_num from " \
          "TB_GPS_1805 t where speed_time >= :1 " \
          "and speed_time < :2 and vehicle_num = '浙ATE638' and state = 1 order by speed_time "

    tup = (begin_time, end_time)
    cursor = conn.cursor()
    cursor.execute(sql, tup)
    veh_trace = {}
    static_num = {}
    for item in cursor.fetchall():
        lng, lat = map(float, item[0:2])
        if 119 < lng < 121 and 29 < lat < 31:
            px, py = bl2xy(lat, lng)
            state = int(item[3])
            stime = item[2]
            speed = float(item[4])
            car_state = int(item[5])
            ort = float(item[6])
            veh = item[7][-6:]
            # if veh != 'AT0956':
            #     continue
            taxi_data = TaxiData(veh, px, py, stime, state, speed, car_state, ort)
            try:
                veh_trace[veh].append(taxi_data)
            except KeyError:
                veh_trace[veh] = [taxi_data]
            try:
                static_num[veh] += 1
            except KeyError:
                static_num[veh] = 1
    new_dict = {}
    for veh, trace in veh_trace.iteritems():
        new_trace = []
        last_data = None
        for data in trace:
            esti = True
            if last_data is not None:
                dist = calc_dist([data.px, data.py], [last_data.px, last_data.py])
                dt = (data.stime - last_data.stime).total_seconds()
                # 过滤异常
                if dt <= 10:
                    esti = False
                elif data.car_state == 1:  # 非精确
                    esti = False
                elif dist < 15:  # GPS的误差在10米，不准确
                    esti = False
            last_data = data
            if esti:
                new_trace.append(data)
                # print i, dist
                # i += 1
        new_dict[veh] = new_trace
    # print "all car:{0}, ave:{1}".format(len(static_num), len(trace) / len(static_num))
    cursor.close()
    conn.close()
    return new_dict

