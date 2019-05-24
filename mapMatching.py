# -*- coding: utf-8 -*-
# @Time    : 2019/5/17 14:30
# @Author  : yhdu@tongwoo.cn
# @简介    :
# @File    : mapMatching.py

from time import clock
from geo import point2segment, point_segment_prob, calc_include_angle3, calc_point_dist, \
    route_trans_prob, path_forward
from map_struct import Segment
from map_info.readMap import ORT_DBWAY
import Queue


MAX_OFFSET = 60


class Candidate(object):
    def __init__(self, line, seq):
        self.line, self.seq = line, seq
        self.uid = self.line.lid * 100 + seq

    def __hash__(self):
        return self.uid

    def __eq__(self, other):
        return self.uid == other.uid


class MatchPoint(object):
    def __init__(self, x, y, line, seq, ort, prob, dist, state):
        self.x, self.y = x, y   # projection point
        self.line, self.seq, self.ort = line, seq, ort
        self.idx = None                 # index in MatchRecord
        self.prob = prob                # emit probability
        self.dist = dist                # dist
        self.state = state              # 0: on segment  1 or 2: not on segment
        self.fact_prob = None           # these below are updated when calculating best index
        self.best_last_idx = None


class TransInfo(object):
    def __init__(self, cur_idx, last_idx, route_dist, prob):
        self.cur_idx, self.last_idx = cur_idx, last_idx     # index in match records
        self.route_dist = route_dist        # route from last point to current point
        self.prob = prob                    # trans probability
        self.line_path = []         # line and point to record path, speed
        self.pt_path = []


class MatchRecord(object):
    """
    each point has one MatchRecord, contains of MatchPoints, TransInfo to last point
    """
    def __init__(self):
        self.match_point_list = []          # MatchPoint
        self.trans_list = []                # TransInfo, update when call "get_trans_matrix"
        self.best_idx = None                # chosen MatchPoint index
        self.best_trans = None              # chosen TransInfo

    def add_match_point(self, match_point):
        match_point.idx = len(self.match_point_list)
        self.match_point_list.append(match_point)

    def add_trans_info(self, ti):
        self.trans_list.append(ti)


class LinePath(object):
    def __init__(self, dist, line, ort):
        self.dist, self.line, self.ort = dist, line, ort


class PrevState(object):
    """
    take line and direction for path
    """
    def __init__(self, line, point, ort):
        self.line, self.point, self.ort = line, point, ort


class SearchNode(object):
    def __init__(self, point, priority):
        self.priority = priority
        self.point = point

    def __lt__(self, other):
        return self.priority < other.priority


class DistConfig(object):
    def __init__(self, euclid_dist, dist_thread, min_dist_thread):
        self.euclid_dist, self.dist_thread, self.min_dist_thread = euclid_dist, dist_thread, min_dist_thread


def debug_time(func):
    def wrapper(*args, **kwargs):
        bt = clock()
        a = func(*args, **kwargs)
        et = clock()
        print "mm.py", func.__name__, "cost", round(et - bt, 2), "secs"
        return a
    return wrapper


@debug_time
def match_trace(trace, map_info):
    """
    :param trace: TaxiData
    :param map_info: MapInfo
    :return: 
    """
    if len(trace) == 0:
        return
    trace_match = []        # MatchRecord
    for i, gps_data in enumerate(trace):
        # 1. find all possibility
        candidate = get_candidate(gps_data, map_info)
        # 2. calculate emit prob.
        ramp, map_index = match_single(candidate, trace, i, trace_match)
        # 3. calculate trans prob.
        if i > 0:
            match_latter(map_index, trace, i, trace_match, ramp)
        # 4. global prob. dynamic programming -- as hidden markov model
        match_best(trace_match, i)
    # 5. find path
    global_match(trace_match)
    over = True


def check_line_projection(line_dist, gps_point, line_desc):
    line, seq = line_desc.line, line_desc.seq
    lid = line.lid
    p0, p1 = line.point_list[seq:seq + 2]

    dist = point2segment(gps_point, p0, p1)
    if dist > MAX_OFFSET:
        return
    try:
        if dist < line_dist[lid][1]:
            line_dist[lid] = [seq, dist]
    except KeyError:
        line_dist[lid] = [seq, dist]


def get_candidate(gps_point, map_info):
    """
    first step, find the nearest candidate edges
    :param gps_point: Point 
    :param map_info: 
    :return: 
    """
    xy_list = [[gps_point.x, gps_point.y]]
    idx, dst = map_info.kdt.query_radius(xy_list, r=500, return_distance=True)
    point_list, line_list = map_info.point_list, map_info.line_list
    line_dist = {}      # make sure that each line has only one matching point
    # { lid: [seq, dist] }
    for i in idx[0]:
        pt = point_list[i]
        for ld, mp in pt.link_list:
            check_line_projection(line_dist, gps_point, ld)
        for ld, mp in pt.rlink_list:
            check_line_projection(line_dist, gps_point, ld)

    match_set = set()
    for lid, match_item in line_dist.iteritems():
        seq, dist = match_item[:]
        cnd = Candidate(line_list[lid], seq)
        # print hash(cnd)
        match_set.add(cnd)
    return match_set


def match_single(candidate_set, trace, idx, match_records):
    """
    :param candidate_set: from get_candidate
    :param trace: 
    :param match_records: outer, store list of MatchRecord
    :param idx: trace[idx] -- current taxi data
    :return: 
    """
    cur_i, last_i, next_i = idx, idx - 1, idx + 1
    if last_i < 0:
        last_i += 1
    if next_i == len(trace):
        next_i -= 1
    cur_pt, last_pt, next_pt = trace[cur_i], trace[last_i], trace[next_i]
    line_mp = {}        # nearest point for each line
    for cnd in candidate_set:
        line, seq = cnd.line, cnd.seq
        lid = line.lid
        if line.rank == u'连杆道路':
            continue
        segment = Segment(line.point_list[seq], line.point_list[seq + 1])
        p, dist, state, proj = point_segment_prob(cur_pt, segment)
        s0 = Segment(last_pt, cur_pt)
        angle0 = calc_include_angle3(s0, segment)
        swap = False
        if angle0 < 0 and line.ort == ORT_DBWAY:
            angle0, swap = -angle0, True
        s1 = Segment(cur_pt, next_pt)
        angle1 = calc_include_angle3(s1, segment)
        if angle1 < 0 and line.ort == ORT_DBWAY:
            angle1, swap = -angle1, True
        if angle0 < 0.5 and angle1 < 0.5 and line.rank != u'匝道':
            continue
        px, py = proj[:]
        mp = MatchPoint(px, py, line, seq, swap, p, dist, state)
        try:
            if dist < line_mp[lid].dist:
                line_mp[lid] = mp
        except KeyError:
            line_mp[lid] = mp
    in_seg = False

    for lid, mp in line_mp.iteritems():
        if mp.state == 0:
            in_seg = True
    ramp_mode = False
    map_index = {}          # return if line has matching for current point
    match_record = MatchRecord()
    for lid, mp in line_mp.iteritems():
        if in_seg and mp.state != 0 and mp.dist > 20:
            continue
        if mp.line.rank == u'匝道':
            ramp_mode = True
        map_index[lid] = mp
        match_record.add_match_point(mp)

    match_records.append(match_record)
    return ramp_mode, map_index


def find_object_match(map_index, cur_lid, cur_seq):
    """
    :param map_index: 
    :param cur_lid: MapSegment
    :param cur_seq: 
    :return: 
    """
    try:
        mp = map_index[cur_lid]
        return True if mp.seq == cur_seq else False
    except KeyError:
        return False


def init_search_param(trace, trace_idx, last_match_point, ramp):
    cur_point = trace[trace_idx]
    euclid_dist = calc_point_dist(last_match_point, cur_point)
    min_dist_thread = 1.5 * euclid_dist
    dist_thread = 6 * euclid_dist if ramp else 3 * euclid_dist
    min_dist = {}
    come_from = {}
    frontier = Queue.PriorityQueue()  # SearchNode
    return cur_point, euclid_dist, min_dist_thread, dist_thread, min_dist, come_from, frontier


def init_queue(queue, map_index, last_mp, match_record, euclid_dist, cur_point, min_dist, come_from):
    """
    get first Search Node in queue
    :param queue: 
    :param map_index: 
    :param last_mp: 
    :param match_record: 
    :param euclid_dist: 
    :param cur_point: 
    :param min_dist: { MapPoint: dist(double) }  record current dist for each point visited
    :param come_from: { MapPoint: PrevState }
    :return: void
    """
    # check if in same segment
    lid, seq = last_mp.line.lid, last_mp.seq
    if find_object_match(map_index, lid, seq):
        cur_mp = map_index[lid]
        dist = calc_point_dist(cur_mp, last_mp)
        # if projection into the other line and (of course) it's too near, we should not take it into account
        # this code will happen again next
        if dist > 0.3 * euclid_dist:
            fact_dist = calc_point_dist(cur_mp, last_mp)
            ti = TransInfo(cur_idx=cur_mp.idx, last_idx=last_mp.idx,
                           route_dist=dist, prob=route_trans_prob(euclid_dist, fact_dist))
            ort = path_forward(last_mp, cur_mp, last_mp.line, seq)
            path = LinePath(dist, last_mp.line, ort)
            ti.line_path.append(path)
            match_record.add_trans_info(ti)

    # add two endpoints in segment
    line = last_mp.line
    pt_fwd, pt_back = line.point_list[seq + 1], line.point_list[seq]
    min_dist[pt_fwd] = calc_point_dist(pt_fwd, last_mp)
    min_dist[pt_back] = calc_point_dist(pt_back, last_mp)

    if line.ort == ORT_DBWAY:
        hx = calc_point_dist(pt_back, cur_point)
        fx = hx + min_dist[pt_back]
        queue.put(SearchNode(pt_back, fx))
        last_state = PrevState(line, None, False)
        come_from[pt_back] = last_state
    hx = calc_point_dist(pt_fwd, cur_point)
    fx = hx + min_dist[pt_fwd]
    queue.put(SearchNode(pt_fwd, fx))
    last_state = PrevState(line, None, True)
    come_from[pt_fwd] = last_state


def search_node(queue, map_index, match_record, dist_config, last_match_point,
                dest_pt, min_dist, come_from, ramp):
    """
    after first step, then begin to search Node
    if found, add new trans info into match record
    we need to find all the points matched, so add dist_thread param to prune
    search with a* algorithm
    heuristic function using euclid distance from current node to target node(fact gps point)
    priority = heuristic function + route dist already
    :param queue: PriorityQueue, contains of SearchNode
    :param map_index: 
    :param match_record: 
    :param dist_config: min_dist_thread -- lower bound of dist_thread, for dist_thread will be changed in searching
                        dist_thread -- upper bound of current dist, break when exceed
                        euclid_dist -- dist from last point to current point
    :param last_match_point
    :param dest_pt: target point calculating heuristic function ( cur gps data in fact )
    :param min_dist: 
    :param come_from: 
    :param ramp
    :return: void
    """
    min_dist_thread, dist_thread, euclid_dist = dist_config.min_dist_thread, \
        dist_config.dist_thread, dist_config.euclid_dist
    while not queue.empty():
        cur_node = queue.get()
        cur_fx, cur_pt = cur_node.priority, cur_node.point
        if cur_fx > dist_thread:
            break
        # bfs
        for ld, next_pt in cur_pt.link_list:
            line, seq, ort = ld.line, ld.seq, ld.ort
            # search next node
            dist = calc_point_dist(cur_pt, next_pt)
            h_dist = calc_point_dist(next_pt, dest_pt)
            next_dist = dist + min_dist[cur_pt]
            change = False
            try:
                if next_dist < min_dist[next_pt]:
                    change = True
            except KeyError:
                change = True
            if change:
                min_dist[next_pt] = next_dist
                next_node = SearchNode(next_pt, h_dist + next_dist)
                queue.put(next_node)
                state = PrevState(line, cur_pt, ort)
                come_from[next_pt] = state

            if change and find_object_match(map_index, line.lid, seq):       # still has one target point: cur point
                cur_mp = map_index[line.lid]
                dist = calc_point_dist(cur_mp, cur_pt)             # last step
                fact_dist = calc_point_dist(cur_mp, last_match_point)
                route_dist = dist + min_dist[cur_pt]
                if fact_dist > 0.3 * euclid_dist:
                    ti = TransInfo(cur_idx=cur_mp.idx, last_idx=last_match_point.idx, route_dist=route_dist,
                                   prob=route_trans_prob(euclid_dist, route_dist))
                    ort = path_forward(cur_pt, cur_mp, line, seq)
                    path = LinePath(dist, line, ort)
                    ti.line_path.append(path)
                    pt = cur_pt
                    while pt is not None:
                        last_state = come_from[pt]
                        last_line, last_point, last_ort = last_state.line, last_state.point, last_state.ort
                        if last_point is None:              # already first point(last_match_point)
                            dist = calc_point_dist(last_match_point, pt)
                        else:
                            dist = calc_point_dist(pt, last_point)
                        path = LinePath(dist, last_line, last_ort)
                        ti.line_path.append(path)
                        pt = last_point
                    ti.line_path.reverse()
                    match_record.add_trans_info(ti)

                    # update thread
                    if not ramp:
                        dist_thread = max(min_dist_thread, min(dist_thread, ti.route_dist * 1.25))


def get_trans_matrix(map_index, last_match_point, match_record, trace, trace_idx, ramp):
    """
    begin a* search from last matchPoint, then find all the match points in current matchRecord
    several params below extends from "match_latter"
    :param map_index: 
    :param last_match_point: last MatchPoint, contains of px, py, ....
    :param match_record: current MatchRecord, contains all the match points
    :param trace: 
    :param trace_idx:  for debug
    :param ramp: 
    :return: TransInfo
    """
    cur_point, euclid_dist, min_dist_thread, dist_thread, \
        min_dist, come_from, frontier = init_search_param(trace, trace_idx, last_match_point, ramp)
    dist_config = DistConfig(euclid_dist, dist_thread, min_dist_thread)

    init_queue(frontier, map_index, last_match_point, match_record, euclid_dist, cur_point, min_dist, come_from)
    search_node(frontier, map_index, match_record, dist_config, last_match_point, cur_point, min_dist, come_from, ramp)


def match_latter(map_index, trace, trace_idx, match_records, ramp):
    """
    :param map_index: { lid: MatchPoint }
    :param trace: 
    :param trace_idx: 
    :param match_records: [MatchRecord]
    :param ramp: if ramp
    :return: 
    """
    # function called after second point. make single match
    # here, we are sure match records has at least 2 items

    last_rec, cur_rec = match_records[-2:]
    max_fact_prob = -1e20
    for mp in last_rec.match_point_list:
        max_fact_prob = max(max_fact_prob, mp.fact_prob)
    # record last max_fact_prob, when too far away to prune

    for i, last_mp in enumerate(last_rec.match_point_list):
        if last_mp.fact_prob < max_fact_prob - 250:
            continue
        get_trans_matrix(map_index, last_mp, cur_rec, trace, trace_idx, ramp)


def match_best(match_records, idx):
    """
    probability DP: step 1, find the maximum with each joint node 
    :param match_records: 
    :param idx: 
    :return: 
    """
    cur_rec = match_records[idx]
    if len(cur_rec.trans_list) == 0:
        for mp in cur_rec.match_point_list:
            mp.fact_prob = mp.prob
            mp.best_last_idx = -1
    else:
        last_rec = match_records[idx - 1]
        for mp in cur_rec.match_point_list:
            mp.fact_prob = -1e10
            mp.best_last_idx = -1
        trans = False
        for ti in cur_rec.trans_list:
            last_idx, cur_idx = ti.last_idx, ti.cur_idx
            last_mp, cur_mp = last_rec.match_point_list[last_idx], cur_rec.match_point_list[cur_idx]
            trans_prob = ti.prob
            fp = last_mp.fact_prob + trans_prob + cur_mp.prob
            if fp > cur_mp.fact_prob:
                cur_mp.fact_prob = fp
                cur_mp.best_last_idx = last_idx
                trans = True
        if not trans:
            for mp in cur_rec.match_point_list:
                mp.fact_prob = -1e10
                mp.best_last_idx = -1


def global_match(match_records):
    """
    probability DP: step 2, find global path
    :param match_records: [MatchRecord]
    :return: 
    """
    best_idx = -1
    # MP(match point) chosen index in match_record.match_point_list
    # here we use index for these codes are copied from C++
    # you can rewrite pythonic codes

    for rec in reversed(match_records):
        if best_idx == -1:
            max_prob, sel = -1e10, -1
            # as the final point, find the match point with maximum prob.
            # then begin reverse
            for j, mp in enumerate(rec.match_point_list):
                if mp.fact_prob > max_prob:
                    max_prob, sel = mp.fact_prob, j
                    best_idx = mp.best_last_idx
            rec.best_idx = sel
        else:
            # recursive
            rec.best_idx = best_idx
            best_idx = rec.match_point_list[best_idx].best_last_idx
        min_path = 1e10
        for ti in rec.trans_list:
            if ti.cur_idx == rec.best_idx and ti.last_idx == best_idx and ti.route_dist < min_path:
                rec.best_trans, min_path = ti, ti.route_dist

