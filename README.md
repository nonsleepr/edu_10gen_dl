##Download course videos from eudcation.10gen.com.

File `config.py` should be populated with login/password.

This script uses code from [youtube-dl](https://github.com/rg3/youtube-dl/) project to download videos.

Script will skip already downloaded videos, although it will look for video links on 10gen's site.

###Dependencies:
* Python 2.7
* Mechanize
* BeautifulSoup4

###Format:
`python edu_10gen.py`