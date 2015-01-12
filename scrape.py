from bs4 import BeautifulSoup

file = open('detail.html')
soup = BeautifulSoup(file)
# soup.prettify()

orders = soup.select("#order_detail")
for order in orders:
    header = order.find(name='h4')
    s = 0
    for string in header.stripped_strings:
        s += 1
        print('{}: {}'.format(s, string))