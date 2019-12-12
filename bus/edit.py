# -*- coding: utf-8 -*-
# @Time    : 2019/11/18 15:42
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : edit.py


import xlrd
import cx_Oracle
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


def main():
    x0 = xlrd.open_workbook(u"线路.xlsx")
    x1 = xlrd.open_workbook("37.xlsx")
    sht0 = x0.sheet_by_index(0)
    sht1 = x1.sheet_by_index(0)
    check_type = {}
    n0 = sht0.nrows
    for i in range(2, n0):
        name = sht0.cell_value(i, 0)
        stop0 = sht0.cell_value(i, 1)
        stop1 = sht0.cell_value(i, 6)
        if stop1 == u"":
            # 55路
            stop1 = stop0
            str_stop = stop0 + u"--" + stop1
            str_total = name + u"," + str_stop
            str_type = name + u"上行"
            check_type[str_total] = str_type
        else:
            str_stop = stop0 + u"--" + stop1
            str_total = name + u"," + str_stop
            str_type = name + u"上行"
            check_type[str_total] = str_type
            str_stop = stop1 + u"--" + stop0
            str_total = name + u"," + str_stop
            str_type = name + u"下行"
            check_type[str_total] = str_type

    conn = cx_Oracle.connect('hzczdsj/tw85450077@192.168.0.80/orcl')
    cur = conn.cursor()
    sql = "select * from tb_bus_route_time"
    cur.execute(sql)
    tm_dict = {}
    for item in cur:
        name, tm = item
        tm_dict[name] = tm
    cur.close()
    conn.close()

    n = sht1.nrows
    for i in range(1, n):
        name = sht1.cell_value(i, 0)
        stop = sht1.cell_value(i, 1)
        str_name = name + ',' + stop
        # str_name = str_name.encode('utf-8')
        try:
            str_type = check_type[str_name].encode('utf-8')
        except KeyError:
            print "error", str_name
            continue
        try:
            print tm_dict[str_type]
        except KeyError:
            print str_type
        pass


main()
