# -*- coding: utf-8 -*-
# @Time    : 2019/10/18 9:52
# @Author  : yhdu@tongwoo.cn
# @简介    : 
# @File    : history.py


import cx_Oracle
from collections import defaultdict


def main():
    try:
        conn = cx_Oracle.connect('hz/hz@192.168.11.88/orcl')
        cur = conn.cursor()
        sql = "select rid, speed, ort, cnt from tb_road_speed_pre"
        cur.execute(sql)
        speed = defaultdict(list)
        for item in cur:
            rid, spd, ort, cnt = item
            speed[(rid, ort)].append((spd, cnt))
        tup_list = []
        for ln, spd_list in speed.items():
            t, w = 0, 0
            for spd, cnt in spd_list:
                t, w = t + spd * cnt, w + cnt
            ln_spd = t / w
            rid, ort = ln
            tup_list.append((rid, ort, ln_spd, w))
        sql = "delete from tb_road_his_speed"
        cur.execute(sql)

        sql = "insert into tb_road_his_speed (rid, ort, speed, cnt) values(:1, :2, :3, :4)"
        cur.executemany(sql, tup_list)
        conn.commit()
        cur.close()
        conn.close()
    except cx_Oracle.DatabaseError:
        print "oracle error"


if __name__ == '__main__':
    main()
