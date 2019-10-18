# -*- coding: utf-8 -*-
# @Time    : 2019/10/18 14:41
# @Author  : yhdu@tongwoo.cn
# @简介    : 找到计价器有问题，一直重车的车辆
# @File    : exclude.py


from fetchData import get_all_data
from datetime import datetime, timedelta
import cx_Oracle


def ex():
    bt = datetime(2018, 5, 1)
    ft = datetime(2018, 5, 8)
    filter_veh = set()
    while bt < ft:
        et = bt + timedelta(hours=4)
        trace_dict = get_all_data(True, bt, et)
        for veh, trace in trace_dict.items():
            off_cnt, on_cnt = 0, 0
            for data in trace:
                if data.state == 0:
                    off_cnt += 1
                else:
                    on_cnt += 1
            if off_cnt == 0 and on_cnt > 240:
                # print veh, on_cnt
                filter_veh.add(veh)
        bt += timedelta(days=1)
    return filter_veh


def main():
    fs = ex()
    conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
    cursor = conn.cursor()
    sql = "delete from tb_all_on"
    cursor.execute(sql)
    sql = "insert into tb_all_on values(:1)"
    tup_list = []
    for veh in fs:
        tup_list.append((veh, ))
    cursor.executemany(sql, tup_list)
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
