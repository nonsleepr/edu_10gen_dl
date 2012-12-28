##Download course videos from education.10gen.com or any other site 'Powered by EdX' (including, of course, http://edx.org itself).

File `config.py` should be populated with login/password and site you're downloading video from.

This script uses code from [youtube-dl](https://github.com/rg3/youtube-dl/) project to download videos.

Accepts destination path as optional parameter.

###Dependencies:
* Python 2.7
* Mechanize
* BeautifulSoup4

###Format:
+ `python edu_10gen.py`
+ `python edu_10gen.py c:\Users\MyUser\Lectures\`
