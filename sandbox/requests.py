        self.rec('Mining the following day: {}', day.strftime('%d.%m.%Y'))


Now we are going to make a POST request with that request. This bit uses urllib to encode the POSTDATA.

#import needed modules
import urllib
import urllib2

#make a string to hold the url of the request
url = "http://www.webmalt.com/"

#place POST data in a dictionary
post_data_dictionary = {'name':'Devin Cornell', "age":18, "favorite OS":"Ubuntu"}

#encode the POST data to be sent in a URL
post_data_encoded = urllib.urlencode(post_data_dictionary)

#make a request object to hold the POST data and the URL
request_object = urllib2.Request(url, data)

#make the request using the request object as an argument, store response in a variable
response = urllib2.urlopen(request_object)

#store request response in a string
html_string = response.read()

Now we will make a request that sends POST data, and also changes the HTTP headers used with the request.

import urllib
import urllib2
url = "http://www.webmalt.com"
post_data_dictionary = {"firstname":"Devin", "lastname":"Cornell"}

#sets the user agent header
http_headers = {"User-Agent":"Mozilla/4.0 (compatible; MSIE 5.5;Windows NT)"}

post_data_encoded = urllib.urlencode(post_data_dictionary)
request_object = urllib2.Request(url, post_data_encoded, http_headers)

response = urllib2.urlopen(request_object)
html_string = response.read()

Here is how to handle an exception to a request. This will help with troubleshooting.

import urllib2
request = urllib2.Request("http://www.nonexistant_server.org")
#uses try statement to handle possible failure
try:
   urllib2.urlopen(request_object)
#uses except statement to detect a URLError  problem that was created by urllib2 by the failed request, then stores more info in an exception_variable
except URLError, exception_variable:
   #prints the reason for failure out to help debugging
   print exception_variable.reason

There may also be a case where the URL finds a target, but that target replies with an http error page and code. The code here is the same as above, but this time uses “except HTTPError” instead of “except URLError”.

import urllib2
request = urllib2.Request("http://www.nonexistant_server.org")
#uses try statement to handle possible failure
try:
   urllib2.urlopen(request_object)
#uses except statement to detect a HTTPError  problem that was created by
#urllib2 by the failed request, then stores more info in an exception_variable
except HTTPLError, exception_variable:
   #prints the HTTP error code that was given
   print exception_variable.code

Now we are going to learn how to change the HTTP headers to provide for a way to do Basic HTTP Authentication.

import urllib2
import base64
import re

password = "password"

url = "http://www.example_site.com/"
request_object = urllib2.Request(url)
try:
   #make request to server to figure out what type of authentication it uses
   doc = urllib3.urlopen(request_object)
except IOError, error:
   if hasattr(e, 'code'):
      if e.code == 401:
         #host needs authentication, continuing

authentication_string = error.headers['www-authenticate']

#make regular expression to detect authentication realm
regex = re.compile(r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]''', re.IGNORECASE)

#runs the match method to find all matches of the expression
match = regex.match(auth_string)

scheme = match.group(1)
realm = match.group(2)
if scheme.lower() == 'basic':
   #the server requires basic authentication

request = urllib2.Request(url)

#encode the desired password in base 64 encoding
encoded_string = base64.encodestring('%s:%s' % (username, password))[:-1]

request.add_header("Authorization", "Basic %s" % encoded_string)

try:
   document = urllib2.urlopen(request)
except IOError:
   #the password was not correct

#if the exception wasn't raised, the password was correct, and doc.read() will give the data

The last thing to cover will be the ability to download files and save them to the hard drive. This could be a useful task for downloading many files systematically.

import urllib2

#make a variable to hold the name of the file that was written to
file_name = "website.html"

url = "http://example.com"
response = urllib2.urlopen(url)

#open a local file for writing
local_file = open(file_name, "w")

#read from request while writing to file
local_file.write(response.read())
local_file.close()

And that is all you need to know to effectively use urllib2, the swiss army blade of web requests in Python. Stay tuned for other articles on very useful modules in Python and other languages!

Sources: http://www.techniqal.com/blog/2008/07/31/python-file-read-write-with-urllib2/