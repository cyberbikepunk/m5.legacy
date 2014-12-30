
from datetime import timedelta, date

# construct a list a string dates
days = calendar.Calendar().itermonthdates(2014,11)
print days

for day in days:
	date_string = day.strftime('%d.%m.%Y')
	date_url = 'http://bamboo-mec.de/ll_detail.php5?status=delivered&datum=' + '01.12.2014' #date_string
	print date_url
	date_request = session.get(date_url)
	print(date_request.status_code)
	print(date_request.text)
	date_file = open(date_string + '.html', 'w')
	#print date_file.encoding
	#date_file.write(date_request.text)
	date_file.close()