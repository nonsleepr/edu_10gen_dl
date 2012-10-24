##Generate list of course videos from eudcation.10gen.com.

File `config.py` should be populated with login/password.

After completion, the script will create text file with youtube links, named after the course.
This file could then be used to download videos with [youtube-dl](https://github.com/rg3/youtube-dl/).

###Dependencies:
* Python 2.7
* Mechanize
* BeautifulSoup4

###Format:
`python edu_10gen.py`