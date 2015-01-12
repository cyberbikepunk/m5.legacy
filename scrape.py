from bs4 import BeautifulSoup
import re

file = open('19.12.2014-2974278.html')
soup = BeautifulSoup(file)
order = soup.find(id='order_detail')
fields = dict()

# Grab the client name and number
client_info = order.find(name='h4')
strings = list(client_info.stripped_strings)
match = re.match(r'Kunde:\s(.*)\s\|\s(\d{5})', strings[0])
fields['client_name'] = match.group(1)
fields['client_number'] = match.group(2)

# Grab the job id and the payment method
job_info = order.find(name='h2')
strings = list(job_info.stripped_strings)
match = re.match(r'(?:BAR\s)?(\d{10})', strings[0])
fields['id'] = match.group(1)

# Grab the the price information
price_info = order.find(name='tbody')
strings = list(price_info.stripped_strings)
# rearrange a one-dimensional list of cells
# into a dictionary
sub_items = strings[1::2]
sub_total = strings[::2]
prices = dict(zip(sub_total, sub_items))
# Substitute german with english keys
KEYS = [('Stadtkurier', 'city_tour'),
        ('OV.', 'overnight'),
        ('EmpfangsbestÃ¤t.',  'same_day_fax_return'),
        ('Wartezeit min.',  'waiting_time')]
for old, new in KEYS:
    if old in prices:
        prices[new] = prices.pop(old)
fields.update(prices)
print(fields)

# Grab all pick-ups and drop-offs
stops_info = order.find_all(name='div', attrs={'data-collapsed': 'true'})
for stop_info in stops_info:
    strings = list(stop_info.stripped_strings)
    print(strings)