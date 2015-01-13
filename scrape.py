from bs4 import BeautifulSoup
import re

file = open('19.12.2014-2974278.html')
order = BeautifulSoup(file).find(id='order_detail')
fields = dict()

# Grab the client name and number
client_html = order.find(name='h4')
strings = list(client_html.stripped_strings)
print(strings)
match = re.match(r'Kunde:\s(.*)\s\|\s(\d{5})', strings[0])
fields['client_name'] = match.group(1)
fields['client_number'] = match.group(2)

# Grab the job id and the payment method
job_html = order.find(name='h2')
strings = list(job_html.stripped_strings)
match = re.match(r'(?:BAR\s)?(\d{10})', strings[0])
fields['id'] = match.group(1)

# Grab the the price information
price_html = order.find(name='tbody')
strings = list(price_html.stripped_strings)
# rearrange a one-dimensional list of cells
# into a dictionary
items = strings[1::2]
subtotal = strings[::2]
prices = dict(zip(subtotal, items))
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
stops = list()
stops_html = order.find_all(name='div', attrs={'data-collapsed': 'true'})
for stop_html in stops_html:
    stop_type_html = stop_html.find(name='h3')
    print(stop_type_html)
    strings = list(stop_type_html.stripped_strings)
    match = re.match(r'(Abholung)', strings[0])
    fields['pick_up'] = True if match else False
    match = re.match(r'(Zustellung)', strings[0])
    fields['drop_off'] = True if match else False
    print(fields)
    exit()
    items = stop_html.contents
    print(items)
    strings = list(stop_html.stripped_strings)
    print(strings)