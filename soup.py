from bs4 import BeautifulSoup

file = open('detail.html')
soup = BeautifulSoup(file)
orders = soup.select("#order_detail")
# print(type(orders[0]))
for order in orders:
    # print(order.contents)
    for content in order.contents:
        pass
        # print(content)
    for child in order.children:
        # print(child)
        text = child.string
        #  print(text)
    header = order.find(name='h4')
    print(header)
    print(type(header))
    print(header.contents)
    stops = order.find_all(name='div', attrs={'data-collapsed': 'true'})
    for stop in stops:
        print(stop)
        print('**************************')
        pass

stops = soup.find_all('div', {'data-collapsed': 'true'})
for stop in stops:
    # print(stop)
    # print('**************************')
    pass

