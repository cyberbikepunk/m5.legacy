from bs4 import BeautifulSoup
import re


def _attributes_blueprints():
    """
    Define the blueprints for the attributes scraper. The order of the
    list is important. Each blueprint contains information about:
        - which tag to target in the DOM
        - which lines to scrape inside the tag
        - what regex pattern to run on each line
        - what fields to return for each line

    :return: (list) A list of blueprint dictionaries
    """
    # Define three blueprints
    attributes_blueprints = list(range(3))

    # General attributes
    attributes_blueprints[0] = {
        'tag': 'h2',
        'lines': [0],
        'patterns': [r'(BAR\s)?(\d{10})'],
        'fields': [['cash_payment', 'id']]
    }
    # Client attributes
    attributes_blueprints[1] = {
        'tag': 'h4',
        'lines': [0],
        'patterns': [r'Kunde:\s(.*)\s\|\s(\d{5})'],
        'fields': [['client_name', 'client_number']]
    }
    # Trip attributes
    attributes_blueprints[2] = {
        'tag': 'p',
        'lines': [0],
        'patterns': [r'(\d{1,2},\d{3})\skm'],
        'fields': [['km']]
    }
    return attributes_blueprints

def _scrape_attributes(blueprint, soup_subset):
    """
    Scrape off the contents contained inside a given html tag
    using the blueprint we've prepared.

    :param blueprint: (dict) The blueprint for the tag contents
    :param soup_subset: (tag object) cleaned up html
    :return: (dict) field name/value pairs
    """
    contents = list(soup_subset.stripped_strings)
    fields = dict()

    for line in blueprint['lines']:
        match = re.match(blueprint['patterns'][line], contents[line])
        for index, name in enumerate(blueprint['fields'][line]):
            # Indices for matched groups start at 1
            fields[name] = match.group(index+1)

    return fields

def _scrape_prices(soup_subset):
    """
    Scrape off the 'prices' table at the bottom of the page. This section is
    scraped seperately precisely because it's already formatted as a table.

    :param soup_subset: (tag object) cleaned up html
    :return: (dict) field name/value pairs
    """
    # The table is grabbed as a one-dimensional list
    # of cells but we want it in dictionary format.
    cells = list(soup_subset.stripped_strings)
    prices_table = dict(zip(cells[::2], cells[1::2]))

    # Original field names are no good. Change them.
    keys = [
        ('Stadtkurier',         'city_tour'),
        ('Stadt Stopp(s)',      'extra_stops'),
        ('OV.',                 'overnight'),
        ('EmpfangsbestÃ¤t.',    'fax_confirm'),
        ('Wartezeit min.',      'waiting_time')
    ]
    for old, new in keys:
        if old in prices_table:
            prices_table[new] = prices_table.pop(old)

    return prices_table

def _address_blueprint():
    """
    Define the blueprint to scrape a single address.

    :return: (dict) A blueprint to scrape addresses
    """
    address_blueprint = {
        'lines': [0, 1, 2, 3, 6, 7],
        'patterns': [
            r'(Abholung)|(Zustellung)',
            r'(.*)',
            r'(.*)',
            r'(\d{5})\s(.*)',
            r'(?:.*)ab\s(\d{2}:\d{2})*(?:.*)bis\s(\d{2}:\d{2})*',
            r'ST:\s(\d{2}:\d{2})'
        ],
        'fields': [
            ['purpose'],
            ['company'],
            ['address'],
            ['postal_code', 'city'],
            ['from', 'until'],
            ['timestamp']
        ]
    }
    return address_blueprint

def _scrape_address(soup_subset):
    """
    Scrape off all fields associated with an address, including for example
    the pick-up or drop-off time window.

    :param soup_subset: (str) cleaned up html
    :return: (dict) field name/value pairs
    """
    blueprint = _address_blueprint()
    contents = list(soup_subset.stripped_strings)
    fields = dict()

    for line_index, line in enumerate(blueprint['lines']):
        print(blueprint['patterns'][line_index])
        match = re.match(blueprint['patterns'][line_index], contents[line])
        for field_index, name in enumerate(blueprint['fields'][line_index]):
            # Indices for matched groups start at 1
            fields[name] = match.group(field_index+1)

    return fields

def scrape_job(html):
    """
    Scrape the shit out of the html document using BeautifulSoup
    and a little regex, in three steps: first, job attributes,
    then prices and finally addresses. Attributes and prices
    are returned as dictionaries and addresses as a list of
    dictionaries. Each dictionary contains field name/value
    pairs. All values are raw strings.

    :param html: (tag object) cleaned up html produced by BeautifulSoup
    :return: (tuple) attributes, prices, addresses
    """
    # Scrape various job attributes in various places
    # attributes = dict()
    # for blueprint in _attributes_blueprints():
    #     html_subset = html.find_next(blueprint['tag'])
    #     fields = _scrape_attributes(blueprint, html_subset)
    #     attributes.update(fields)

    # Scrape the prices from the only table on the page
    # html_subset = html.find(name='tbody')
    # prices = _scrape_prices(html_subset)

    # Scrape an arbitrary number of addresses. A normal city tour has
    # usually two addresses but sometimes more. An overnight tour has
    # strictly two addresses, but the second is a delivery point outside
    # of Berlin (and therefore irrelevant). We deal with these issues
    # downstream.
    addresses = list()
    html_subsets = html.find_all(name='div', attrs={'data-collapsed': 'true'})
    for html_subset in html_subsets:
        address = _scrape_address(html_subset)
        addresses.append(address)

    return attributes, prices, addresses

def main():
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
        file_handle = open(f)
        soup = BeautifulSoup(file_handle).find(id='order_detail')
        data = scrape_job(soup)
        print(data)

main()