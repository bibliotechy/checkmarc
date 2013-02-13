checkmarc
=========

checkmarc is a django app that lets you build validation reports for batches of MARC records. Just create a report, add some checks for it to run, and then give it a marc file to validate. It'll spit out  list of records probably need to be inspected along with an indication of which check(s)'s criteria were met.

Install
------
For local development I'm using sqlite, but feel fee to swap in your own DB

1. `sudo apt-get install sqlite3 python-sqlite2`
1. `git clone git://github.com/bibliotechy/checkmarc.git`
1. `cd checkmarc`
1. `pip install -r required.txt`
1. move checkmarc/local-settings.py to checkmarc/settings.py
1  in order for people to login with their github, facebook, twitter, google credentials you will need to create applications on those sites, and fill in oauth keys in your settings.py. For development you can probably get by with just one login provider.
1. `python manage.py syncdb`
1. `python manage.py runserver`
1. point your browser at 127.0.0.1:8000



