from bs4 import BeautifulSoup
import re


def _blueprints():
    """
    Define the blueprints for the section scraper. The order of the list is
    important. Each blueprint contains information about:
        - which tag to target in the DOM
        - which lines to scrape inside the tag
        - what regex pattern to run on each line
        - what fields to return for each line

    :return: (list) A list of blueprint dictionaries
    """
    # Three sections appear strictly once
    blueprints = list(range(3))

    # General information
    blueprints[0] = {
        'tag': 'h2',
        'lines': [0],
        'patterns': [r'(BAR\s)?(\d{10})'],
        'fields': [['cash_payment', 'id']]
    }
    # Client information
    blueprints[1] = {
        'tag': 'h4',
        'lines': [0],
        'patterns': [r'Kunde:\s(.*)\s\|\s(\d{5})'],
        'fields': [['client_name', 'client_number']]
    }
    # Trip information
    blueprints[2] = {
        'tag': 'p',
        'lines': [0],
        'patterns': [r'(\d{1,2},\d{3})\skm'],
        'fields': [['km']]
    }

    # Arbitrary number of stops


    return blueprints

def _scrape_section(bp, source):
    """
    Scrape off a small section contained inside a tag
    with BeautifulSoup and a little regex.

    :param bp: (dict) The blueprint for the section
    :param source: (str) cleaned up html produced by BeautifulSoup
    :return: (dict) field name/value pairs
    """
    contents = list(source.stripped_strings)
    fields = dict()

    for line in bp['lines']:
        match = re.match(bp['patterns'][line], contents[line])
        for index, name in enumerate(bp['fields'][line]):
            # Indices for matched groups start at 1
            fields[name] = match.group(index+1)

    return fields


def scrape_prices(source):
    """
    Scrape the 'prices' table at the bottom of the page. This section is
    scraped seperately precisely because it's already formatted as a table.

    :param source: (str) cleaned up html produced by BeautifulSoup
    :return: (dict) field name/value pairs
    """
    # Grab the only html table in the document
    html_subset = source.find(name='tbody')
    cells = list(html_subset.stripped_strings)

    # The table is returned as a one-dimensional list
    # of cells but we want it in dictionary format.
    prices = dict(zip(cells[::2], cells[1::2]))

    # Original field names are no good. Change them.
    keys = [('Stadtkurier', 'city_tour'),
            ('Stadt Stopp(s)', 'extra_stops'),
            ('OV.', 'overnight'),
            ('EmpfangsbestÃ¤t.',  'fax_return'),
            ('Wartezeit min.',  'waiting_time')]
    for old, new in keys:
        if old in prices:
            prices[new] = prices.pop(old)

    return prices

def main(filename):
    file = open(filename)
    html_source = BeautifulSoup(file).find(id='order_detail')
    fields = dict()

    # Scrape the prices at the bottom of the page
    prices = scrape_prices(html_source)
    fields.update(prices)

    # Scrape multiple subsections of the page
    # using the blueprints we've prepared
    blueprints = _blueprints()
    for blueprint in blueprints:
        html_subset = html_source.find_next(blueprint['tag'])
        fields_subset = _scrape_section(blueprint, html_subset)
        fields.update(fields_subset)

    print(filename)
    print(fields)


filenames = [
    '19.12.2014-2973926.html',
    '19.12.2014-2974276.html',
    '19.12.2014-2974278.html',
    '19.12.2014-2974685.html',
    '19.12.2014-2974730.html',
    '19.12.2014-2974918.html',
    '19.12.2014-2975095.html',
    '19.12.2014-2975147.html',
    '19.12.2014-2976587.html',
    '19.12.2014-2976667.html',
    '19.12.2014-2976786.html',
    '19.12.2014-2977728.html',
    ]
for f in filenames:
    main(f)