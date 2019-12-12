# -*- coding: utf-8 -*-
# @Time    : 2019/11/14 15:04
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : route.py


import xlrd
from collections import defaultdict
from geo import wgs84_to_gcj02
from coord import bl2xy
import cx_Oracle
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


def get_route():
    xls = xlrd.open_workbook(u"线路.xlsx")
    sht = xls.sheet_by_index(1)
    n = sht.nrows
    line_list = defaultdict(list)
    for i in range(1, n):
        name = sht.cell_value(i, 0)
        if name != u'4路':
            continue
        ort = sht.cell_value(i, 1)
        # if ort != u'上行':
        #     continue
        stop_name = sht.cell_value(i, 4)
        lng = float(sht.cell_value(i, 5))
        lat = float(sht.cell_value(i, 6))
        px, py = wgs84_to_gcj02(lng, lat)
        x, y = bl2xy(py, px)
        seq = int(sht.cell_value(i, 9))
        full_name = (name + ort).encode('utf-8')
        line_list[full_name].append((x, y))
    return line_list


def get_route1():
    line_list = defaultdict(list)
    # name = "中河高架南向北"
    # l1, b1 = 120.170807, 30.274136
    # l0, b0 = 120.17454, 30.215114
    # x0, y0 = bl2xy(b0, l0)
    # x1, y1 = bl2xy(b1, l1)
    # line_list[name].append((x0, y0))
    # line_list[name].append((x1, y1))

    # name = "中河高架北向南"
    # line_list[name].append((x1, y1))
    # line_list[name].append((x0, y0))
    #
    # name = "德胜快速路西向东"
    # l0, b0 = 120.150078, 30.290942
    # l1, b1 = 120.382315, 30.323121
    # x0, y0 = bl2xy(b0, l0)
    # x1, y1 = bl2xy(b1, l1)
    # line_list[name].append((x0, y0))
    # line_list[name].append((x1, y1))
    #
    # name = "德胜快速路东向西"
    # line_list[name].append((x1, y1))
    # line_list[name].append((x0, y0))
    #
    # name = "文一路西向东"
    # l0, b0 = 120.086038, 30.286867
    # l1, b1 = 120.144886, 30.288868
    # x0, y0 = bl2xy(b0, l0)
    # x1, y1 = bl2xy(b1, l1)
    # line_list[name].append((x0, y0))
    # line_list[name].append((x1, y1))
    # name = "文一路东向西"
    # line_list[name].append((x1, y1))
    # line_list[name].append((x0, y0))
    #
    name = "凤起路西向东"
    l0, b0 = 120.157424, 30.263073
    l1, b1 = 120.190805, 30.263387
    x0, y0 = bl2xy(b0, l0)
    x1, y1 = bl2xy(b1, l1)
    line_list[name].append((x0, y0))
    line_list[name].append((x1, y1))
    # name = "凤起路东向西"
    # line_list[name].append((x1, y1))
    # line_list[name].append((x0, y0))
    #
    # name = "沈半路北向南"
    # l0, b0 = 120.175294, 30.352016
    # l1, b1 = 120.155388, 30.311602
    # x0, y0 = bl2xy(b0, l0)
    # x1, y1 = bl2xy(b1, l1)
    # line_list[name].append((x0, y0))
    # line_list[name].append((x1, y1))
    # name = "沈半路南向北"
    # line_list[name].append((x1, y1))
    # line_list[name].append((x0, y0))

    return line_list


def delete_route_road():
    conn = cx_Oracle.connect('hzczdsj/tw85450077@192.168.0.80/orcl')
    cur = conn.cursor()
    sql = "delete from tb_bus_road"
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def save_route_road(tup_list):
    conn = cx_Oracle.connect('hzczdsj/tw85450077@192.168.0.80/orcl')
    cur = conn.cursor()
    sql = "insert into tb_bus_road (route_name, seq, distance, rid, ort) values(:1,:2,:3,:4,:5)"
    cur.executemany(sql, tup_list)
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    get_route()
