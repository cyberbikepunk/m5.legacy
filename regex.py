import re

pattern = r'<h2>(?P<id>\d{10})\s{1}\|\s{1}(?P<type>Stadtkurier|Overnight)' \
          r'(?:.|\n)*Kunde:\s(?P<client>(?:.)*)\s\|\s(?P<client_id>\d{5})'
file = open('detail.html')
html = file.read()
print(pattern)

regex = re.compile(pattern)
m = regex.search(html)
if m:
        print(m.groupdict())