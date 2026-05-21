#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2. may. 2014

@author: polz
'''

from bs4 import BeautifulSoup
import urllib2, urllib
import json
import datetime
import re
from collections import defaultdict
# prva stran

#def get_wise_reservations(base_url):
#    return _parse_groups_page(_fetch_groups_page(base_url))

def get_wise_reservations(base_url):
    busy = _get_resrooms_busy_times(base_url)
    return _get_reservation_details(base_url, busy)

def _fetch_resrooms_page(base_url, datestr=None):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', '')]
    #req = urllib2.Request(base_url + 'groups.php', headers=dict())
    # index_page = opener.open(req)
    # index_page = urllib2.urlopen(req)
    if datestr is None:
        page = opener.open(base_url + 'resrooms.php')
    else:
        data = urllib.urlencode({'date_field':datestr,
            'selected_tab': '',
            'dayid_field': "",
            'hourid_field': "",
            "roomid_field": "",
            "description_field": "",
            "log_out": "" })
        page = opener.open(base_url + 'resrooms.php', data=data)
    s = page.read()
    return s
    # read reservations until the first whole week without a single
    # reservation
    p = BeautifulSoup(s).find("select", id='program')
    l = []

def _get_resrooms_busy_times(base_url, start_date = None, 
                            end_date=None,
                            end_empty_days=None):
    if start_date is None:
        now = datetime.datetime.now()
        start_date = datetime.datetime(day=now.day,
            month=now.month, year=now.year)
    if end_empty_days is None and end_date is None:
        end_year = now.year
        if now.month >= 10:
            end_year += 1
        end_date = datetime.datetime(
            month = 10,
            day = 1,
            year = end_year)
    print end_date
    empty_days = 0
    l = []
    d = start_date
    """
    Wise is just so great! Three different functions are used to
        color the cells in the reservation table.
    colCells(room_id, day, time, duration)
    colCellExam(room_id, day, time, beginsAt, is_owner)
    colCell(room_id, day, time, begins_at, is_owner)
    """
    colcells_re = re.compile(r"colCells\((?P<room_id>\d+), *(?P<day>\d+), *(?P<time>\d+), *(?P<duration>\d+)\)")
    colcellexam_re = re.compile(r"colCellExam\((?P<room_id>\d+), *(?P<day>\d+), *(?P<time>\d+), *(?P<begins_at>\d+), *(?P<is_owner>\w+)\)")
    colcell_re = re.compile(r"colCell\( *(?P<room_id>\d+), *(?P<day>\d+) *, *(?P<time>\d+) *, *(?P<begins_at>\d+) *, *(?P<is_owner>\w+) *\)")
    busy_dict = defaultdict(dict)
    classrooms = None
    times = []
    while (end_date is None or d < end_date) and (end_empty_days is None or empty_days < end_empty_days):
        print d, " - empty days:", empty_days
        s = _fetch_resrooms_page(base_url, d.strftime("%d.%m.%Y"))
        bs = BeautifulSoup(s)
        if classrooms is None:
            # first pass
            classrooms = dict()
            heads = bs.find_all("td", {"class":"roomsCell"})
            for h in heads:
                try:
                    head_text = h.find("h4").text
                    if h.attrs.get("align", None) == "center":
                        n = h.next_sibling
                        while not hasattr(n, "attrs") or "id" not in n.attrs:
                            n = n.next_sibling
                        class_id = n.attrs['id']
                        class_id = class_id[1:class_id.find('d')]
                        classrooms[class_id] = head_text
                    else:
                        hours, minutes = head_text.split(":")
                        times.append(datetime.timedelta(hours=int(hours),
                            minutes=int(minutes)))
                except Exception, e:
                    print e
                    pass
                # print class_name.encode("utf-8"), class_id
        p = bs.find_all("script", {"src":None})
        empty_day = True
        for i in p:
            sx = i.string.strip() 
            if sx.startswith("var sel_tab"):
                for r, details_page in [(colcells_re, "details"),
                        (colcellexam_re, "cmt"),
                        (colcell_re, "cmt")]:
                    for m in r.finditer(s):
                        empty_day = False
                        try:
                            begins_at = int(m.group('begins_at'))
                        except IndexError:
                            begins_at = int(m.group('time'))
                        try:
                            duration = int(m.group('duration'))
                        except IndexError:
                            duration = int(m.group('time')) - begins_at + 1
                        room_id = m.group('room_id')
                        day_id = m.group('day')
                        name_tuple = (classrooms[room_id], room_id)
                        t = times[begins_at - 1] + d
                        bd = busy_dict[name_tuple]
                        bd[(t, day_id, begins_at)] = (max(duration, 
                            bd.get((t, day_id, begins_at)[0], 1)), details_page)
                #for m in colcellexam_re.findall(s):
                #    print "exam:", m
                #for m in colcell_re.findall(s):
                #    print "cell", m
                #print sx.encode("utf-8")
        if empty_day:
            empty_days += 1
        else:
            empty_days = 0
        d = d + datetime.timedelta(days=1)
    res = dict()
    for k, v in busy_dict.iteritems():
        l = []
        for start_tuple in sorted(v):
            l.append((start_tuple, v[start_tuple]))
        res[k] = l
    # print times
    # print res
    return res

def _get_reservation_details(base_url, time_classroom_map):
    #opener = urllib2.build_opener()
    #opener.addheaders = [('User-agent', '')]
    l = list()
    for (classroom, classroom_id), times in time_classroom_map.iteritems():
        print "details for", classroom.encode("utf-8")
        for (start, day_id, time_id), (duration, details_page) in times:
            detail_url = base_url + 'room{}.php?id={}&date={} &day={}&time={}&beginsat={}'.format(details_page, str(classroom_id), start.strftime("%d.%m.%Y"), str(day_id), str(time_id), str(time_id))
            # print detail_url
            bs = BeautifulSoup(urllib.urlopen(detail_url).read())
            properties = {'start': start, 
                'end': start + duration * datetime.timedelta(minutes=30),
                'classrooms': [unicode(classroom)],
                'reason': u''}
            for p in bs.find_all('p'):
                # print p
                t = p.text
                if "style" in p.attrs:
                    properties['reason'] = unicode(t)
                for prop, prop_start in [
                    ('reason', 'Opis: '),
                    ('group', 'Skupina: '),
                    ('teacher', 'Izvajalec: ')]:
                    if t.startswith(prop_start):
                        properties[prop] = unicode(t[len(prop_start):])
            # print properties
            if 'group' in properties:
                 properties['groups'] = properties.pop('group').split(', ')
            else:
                 properties['groups'] = []
            if 'teacher' in properties:
                 properties['teachers'] = properties.pop('teacher').split(', ')
            else:
                 properties['teachers'] = []
            l.append(properties)
            # l.append({'start': start_date, 'end': end_date, 'classroom': classroom,'reason': reason, 'group': group, 'teacher': teacher})
    return l 

   

def _fetch_groups_page(base_url):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', '')]
    #req = urllib2.Request(base_url + 'groups.php', headers=dict())
    # index_page = opener.open(req)
    # index_page = urllib2.urlopen(req)
    index_page = opener.open(base_url + 'groups.php')
    s = index_page.read()
    p = BeautifulSoup(s).find("select", id='program')
    l = []
    # s pomocjo helper.php dobi vse letnike vseh programov
    for i in p.find_all("option"):
            l.append(properties)
            # l.append({'start': start_date, 'end': end_date, 'classroom': classroom,'reason': reason, 'group': group, 'teacher': teacher})
    return l 

   

def _fetch_groups_page(base_url):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', '')]
    #req = urllib2.Request(base_url + 'groups.php', headers=dict())
    # index_page = opener.open(req)
    # index_page = urllib2.urlopen(req)
    index_page = opener.open(base_url + 'groups.php')
    s = index_page.read()
    p = BeautifulSoup(s).find("select", id='program')
    l = []
    # s pomocjo helper.php dobi vse letnike vseh programov
    for i in p.find_all("option"):
        if 'value' in i.attrs and len(i['value']) > 0:
            prog_id = i['value']
            # req = urllib2.Request(base_url + "lib/helper.php?type=program&program_id=" + prog_id, headers=dict())
            year_req = opener.open(base_url + "lib/helper.php?type=program&program_id=" + prog_id)
            # year_req = urllib2.urlopen(req)
            year_s = year_req.read()
            if year_s[0:3] == "\xef\xbb\xbf":
                year_s = year_s[3:]
            jsn = json.loads(year_s)
            for j in jsn['result'][1]:
                l.append(j)
    
    groups = []
    for i in l:
        branch_id = i['branch_id']
        branch_req = opener.open(base_url + "lib/helper.php?type=branch&branch_id=" + branch_id)
        branch_s = branch_req.read()
        if branch_s[0:3] == "\xef\xbb\xbf":
            branch_s = branch_s[3:]
        jsn = json.loads(branch_s)
        for j in jsn['groups']:
            groups.append(j)
    
    group_ids = []
    for i in groups:
        group_ids.append(i['groups_id'])
    
    post_params_group = [("group", str(i)) for i in group_ids]
    post_params = post_params_group + [
        #("date_field","11.10.2014"),
        ("iCal_data",""),
        ("pagename","groups"),
        #("program_index","1"),
        #("program_response","11"),
        #("year_index","1"),
        #("year_response","3"),
        #("branch_id","2"),
        #("branch_index","1"
        #("branch_response",""),
        ("groups_index",",".join([str(i) for i in xrange(1, len(group_ids)+1)])),
        ("groups_values",",".join(group_ids)),
        #("groups_response",""),
        ("with_groups","1"),
        ("groups_selector",""),
        ("branch_selector",""),
        ("show_lastchange","1"),
        ("print_selection_details","1"),
        ("show_week_number","1"),
        ("hide_branch_code","1"),
        ("log_out", ""),
        ("show_week", "0")]
    
    req = urllib2.Request(base_url + 'groups.php')
    req.add_data(urllib.urlencode(post_params))
    resp = opener.open(req)
    return resp.read()

def _parse_groups_page(s):
    soup = BeautifulSoup(s)
    l = []
    res_set = set()
    for i in soup.find_all(['span', 'tr']):
        if i.name == 'span' and 'caption' in i.attrs.get('class', []):
            reason = i.text.strip()
        elif i.name == 'tr' and 'data' in i.attrs.get('class', []):
            s = i.find_all('td')
            dayname, date, times, classroom, class_type, group, teacher = s
            start, end = times.text.split(' - ')
            start_date = datetime.datetime.strptime(date.text + start, "%d.%m.%Y %H:%M")
            end_date = datetime.datetime.strptime(date.text + end, "%d.%m.%Y %H:%M")
            res_set.add((start_date, end_date, classroom.text.strip(), reason, group.text.strip(), teacher.text.strip()))
    for start_date, end_date, classroom, reason, group, teacher in res_set:
        l.append({'start': start_date, 'end': end_date, 
            'classrooms': [classroom],
            'reason': reason, 
            'groups': [group], 'teachers': [teacher]})
    return l 

if __name__ == '__main__':
    base_url = settings.WISE_URL
    #f = open('results.html', 'w')
    #f.write(_fetch_groups_page(base_url))
    #f.close()
    #f = open('results.html')
    #print _parse_groups_page(f.read())
    #f.close()
    # print _fetch_resrooms_page(base_url)
    # print _fetch_resrooms_page(base_url, "27.05.2015")
    res = _get_resrooms_busy_times(base_url)
    l = _get_reservation_details(base_url, res)
    #l = get_wise_reservations(base_url)
    print len(l), "reservations"
