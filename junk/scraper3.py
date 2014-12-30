#!/usr/bin/python

import calendar
import requests
import subprocess
import codecs
import job

# homepage url and login data
url = 'http://bamboo-mec.de'
user = {'username': 'm-134', 'password': 'PASSWORD'}
date = {'datum': '19.12.2014', 'status' : 'delivered'}
suffix = '/ll.php5'

# start a session and with the homepage
s = requests.Session()
s.headers.update({'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:31.0) Gecko/20100101 Firefox/31.0'})
home = s.get(url)

print(home.url)
print(home.status_code)
print(home.headers)

try:
	f = open('home.html', 'w') # This will create a new file or overwrite an existing file
	try:
		f.write(home.text) # Write a string to a file
	finally:
		f.close()
except IOError:
	pass


# now login
login = s.post(url + suffix, data=user)

print(login.url)
print(login.status_code)
print(login.headers)

try:
	f = open('login.html', 'w') # This will create a new file or overwrite an existing file
	try:
		f.write(login.text) # Write a string to a file
	finally:
		f.close()
except IOError:
	pass

# Navigate to the right webpage
contents = s.get(url + suffix, params = date)

print(contents.url)
print(contents.status_code)
print(contents.headers)
print(contents.text)

try:
	#f = open('contents.html', 'w') # This will create a new file or overwrite an existing file
	f = codecs.open('contents.html', encoding='utf-8', mode='w')
	try:
		f.write(contents.text) # Write a string to a file
	finally:
		f.close()
except IOError:
	pass

job = job.Job()

# subprocess.call(["firefox", "contents.html"])