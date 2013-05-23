import glob
import json
import mechanize
import re
import sys
import os.path
from bs4 import BeautifulSoup
from math import floor
from random import random
from urllib import urlencode

from youtube_dl.FileDownloader import FileDownloader
from youtube_dl.InfoExtractors  import YoutubeIE
from youtube_dl.utils import sanitize_filename

import config
YDL_PARAMS_FILE = 'ydl_params.json'


login_url = '/login'
dashboard_url = '/dashboard'
youtube_url = 'http://www.youtube.com/watch?v='

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
            domain=config.DOMAIN,
            domain_specified=False,
            domain_initial_dot=False,
            path='/', path_specified=True,
            secure=False, expires=None,
            discard=True,
            comment=None, comment_url=None,
            rest={'HttpOnly': None}, rfc2109=False)


class EdXBrowser(object):
    def __init__(self):
        self._br = mechanize.Browser()
        self._cj = mechanize.LWPCookieJar()
        csrftoken = makeCsrf()
        self._cj.set_cookie(csrfCookie(csrftoken))
        self._br.set_handle_robots(False)
        self._br.set_cookiejar(self._cj)
        self._br.addheaders.append(('X-CSRFToken',csrftoken))
        self._br.addheaders.append(('Referer',config.SITE_URL))
        self._logged_in = False
        with open(YDL_PARAMS_FILE) as fydl:
            self._fd = FileDownloader(json.load(fydl))
            self._fd.add_info_extractor(YoutubeIE())

    def login(self, email, password):
        try:
            login_resp = self._br.open(config.SITE_URL + login_url, urlencode({'email':email, 'password':password}))
            login_state = json.loads(login_resp.read())
            self._logged_in = login_state.get('success')
            if not self._logged_in:
                print login_state.get('value')
            return self._logged_in
        except mechanize.HTTPError, e:
            sys.exit('Can\'t sign in')

    def list_courses(self):
        self.courses = []
        if self._logged_in:
            dashboard = self._br.open(config.SITE_URL + dashboard_url)
            dashboard_soup = BeautifulSoup(dashboard.read())
            my_courses = dashboard_soup.findAll('article', 'my-course')
            i = 0
            for my_course in my_courses:
                course_url = my_course.a['href']
                course_name = my_course.h3.text
                
                if INTERACTIVE:
                    launch_download_msg = 'Download the course [%s]? (y/n)' % (course_name)
                    launch_download = raw_input(launch_download_msg)
                    if (launch_download.lower() == "n"):
                        continue

                i += 1
                courseware_url = re.sub(r'\/info$','/courseware',course_url)
                self.courses.append({'name':course_name, 'url':courseware_url})
                print '[%02i] %s' % (i, course_name)

    def list_chapters(self, course_i):
        self.paragraphs = []
        if course_i < len(self.courses) and course_i >= 0:
            print "Getting chapters..."
            course = self.courses[course_i]
            course_name = course['name']
            courseware = self._br.open(config.SITE_URL+course['url'])
            courseware_soup = BeautifulSoup(courseware.read())
            chapters = courseware_soup.findAll('div','chapter')
            i = 0
            for chapter in chapters:
                chapter_name = chapter.find('h3').find('a').text

                if INTERACTIVE:
                    launch_download_msg = 'Download the chapter [%s - %s]? (y/n)' % (course_name, chapter_name)
                    launch_download = raw_input(launch_download_msg)
                    if (launch_download.lower() == "n"):
                        continue
                
                i += 1
                print '\t[%02i] %s' % (i, chapter_name)
                paragraphs = chapter.find('ul').findAll('li')
                j = 0
                for paragraph in paragraphs:
                    j += 1
                    par_name = paragraph.p.text
                    par_url = paragraph.a['href']
                    self.paragraphs.append((course_name, i, j, chapter_name, par_name, par_url))
                    print '\t[%02i.%02i] %s' % (i, j, par_name)

    def download(self):
        print "\n-----------------------\nStart downloading\n-----------------------\n"
        for (course_name, i, j, chapter_name, par_name, url) in self.paragraphs:
            #nametmpl = sanitize_filename(course_name) + '/' \
            #         + sanitize_filename(chapter_name) + '/' \
            #         + '%02i.%02i.*' % (i,j)
            #fn = glob.glob(DIRECTORY + nametmpl)
            nametmpl = os.path.join(DIRECTORY,
                                    sanitize_filename(course_name),
                                    sanitize_filename(chapter_name),
                                    '%02i.%02i.*' % (i,j))
            fn = glob.glob(nametmpl)
            
            if fn:
                print "Processing of %s skipped" % nametmpl
                continue
            print "Processing %s..." % nametmpl
            par = self._br.open(config.SITE_URL + url)
            par_soup = BeautifulSoup(par.read())
            contents = par_soup.findAll('div','seq_contents')
            k = 0
            for content in contents:
                #print "Content: %s" % content
                content_soup = BeautifulSoup(content.text)
                try:
                    video_type = content_soup.h2.text.strip()
                    video_stream = content_soup.find('div','video')['data-streams']
                    video_id = video_stream.split(':')[1]
                    video_url = youtube_url + video_id
                    k += 1
                    print '[%02i.%02i.%i] %s (%s)' % (i, j, k, par_name, video_type)
                    #f.writelines(video_url+'\n')
                    #outtmpl = DIRECTORY + sanitize_filename(course_name) + '/' \
                    #        + sanitize_filename(chapter_name) + '/' \
                    #        + '%02i.%02i.%i ' % (i,j,k) \
                    #        + sanitize_filename('%s (%s)' % (par_name, video_type)) + '.%(ext)s'
                    outtmpl = os.path.join(DIRECTORY,
                        sanitize_filename(course_name),
                        sanitize_filename(chapter_name),
                        '%02i.%02i.%i ' % (i,j,k) + \
                        sanitize_filename('%s (%s)' % (par_name, video_type)) + '.%(ext)s')
                    self._fd.params['outtmpl'] = outtmpl
                    self._fd.download([video_url])
                except Exception as e:
                    #print "Error: %s" % e
                    pass

if __name__ == '__main__':
    INTERACTIVE = ('--interactive' in sys.argv)

    if len(sys.argv) >= 2:
        DIRECTORY = sys.argv[-1].strip('"')
    else:
        DIRECTORY = os.path.curdir

    edxb = EdXBrowser()
    edxb.login(config.EMAIL, config.PASSWORD)
    edxb.list_courses()
    for c in range(0,len(edxb.courses)):
        edxb.list_chapters(c)
        edxb.download()
