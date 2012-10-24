import os
import re
import sys

import json
from datetime import date

from random import random
from math import floor
from pprint import pprint

from urllib import urlencode

try:
    from bs4 import BeautifulSoup
    import mechanize
except ImportError:
    print ("Not all the nessesary libs are installed. " +
           "Please see requirements.txt.")
    sys.exit(1)

try:
    from config import EMAIL, PASSWORD
except ImportError:
    print "You should provide config.py file with EMAIL and PASSWORD."
    sys.exit(1)

try:
    from config import TARGETDIR
except ImportError:
    TARGETDIR = ''

site_url = 'https://education.10gen.com'
login_url = '/login'
dashboard_url = '/dashboard'
youtube_url = 'http://www.youtube.com/watch?v='

username_xpath = '/html/body/section/section[1]/section[1]/section/ul/li[2]/span[2]'

COOKIEFILE = 'c:/Users/EB186011/cookie_10gen.txt'

def makeCsrf():
    t = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    e = 24
    csrftoken = list()
    for i in range(0,e):
        csrftoken.append(t[int(floor(random()*len(t)))])
    return ''.join(csrftoken)

def csrfCookie(csrftoken):
    return mechanize.Cookie(version=0,
            name='csrftoken',
            value=csrftoken,
            port=None, port_specified=False,
            domain='10gen.com',
            domain_specified=False,
            domain_initial_dot=False,
            path='/', path_specified=True,
            secure=False, expires=None,
            discard=True,
            comment=None, comment_url=None,
            rest={'HttpOnly': None}, rfc2109=False)


br = mechanize.Browser()
cj = mechanize.LWPCookieJar()
csrftoken = makeCsrf()
cj.set_cookie(csrfCookie(csrftoken))
br.set_handle_robots(False)
br.set_cookiejar(cj)
br.addheaders.append(('X-CSRFToken',csrftoken))
br.addheaders.append(('Referer','https://education.10gen.com'))
try:
    login_resp = br.open(site_url + login_url, urlencode({'email':EMAIL, 'password':PASSWORD}))
except mechanize.HTTPError, e:
    print "Unexpected error:", e.code
    exit()
login_state = json.loads(login_resp.read())
if not login_state.get('success'):
    print login_state.get('value')
    exit()

dashboard = br.open(site_url + dashboard_url)
dashboard_soup = BeautifulSoup(dashboard.read())
username = dashboard_soup.find('section', 'user-info').findAll('span')[1].text
print 'Logged as %s\n\n' % username

my_courses = dashboard_soup.findAll('article', 'my-course')
for my_course in my_courses:
    course_url = my_course.a['href']
    course_name = my_course.h3.text
    f = open(course_name + '.txt', 'w')
    print '%s' % course_name
    courseware_url = re.sub(r'\/info$','/courseware',course_url)
    courseware = br.open(site_url+courseware_url)
    courseware_soup = BeautifulSoup(courseware.read())
    chapters = courseware_soup.findAll('div','chapter')
    for chapter in chapters:
        chapter_title = chapter.find('h3').find('a').text
        print '\t%s' % chapter_title
        paragraphs = chapter.find('ul').findAll('li',' ')
        for paragraph in paragraphs:
            par_name = paragraph.p.text
            par_url = paragraph.a['href']
            par = br.open(site_url + par_url)
            par_soup = BeautifulSoup(par.read())
            content = par_soup.findAll('div','seq_contents')[0].text
            content_soup = BeautifulSoup(content)
            video_stream = content_soup.find('div','video')['data-streams']
            video_id = video_stream.split(':')[1]
            video_url = youtube_url + video_id
            print '\t\t%s: %s' % (par_name, video_url)
            f.writelines(video_url+'\n')
    f.close()
    print '\nYou can now downlaod lecture videos with the following command:\n    youtube-dl -a "%s.txt" -A -t\n' % course_name
