from bs4 import BeautifulSoup
import re
import pprint

TAGS = {
    'address': {
        'name': 'div',
        'attrs': {'data-collapsed': 'true'}
    },
    'header': {
        'name': 'h2',
        'attrs': {}
    },
    'client': {
        'name': 'h4',
        'attrs': {}
    },
    'itinerary': {
        'name': 'p',
        'attrs': {}
    },
    'prices': {
        'name': 'tbody',
        'attrs': {}
    }
}

BLUEPRINTS = {  # TODO add transport type and package description
    'address': {
        'company': {'line': 1, 'pattern': r'(.*)', 'optional': False},
        'address': {'line': 2, 'pattern': r'(.*)', 'optional': False},
        'city': {'line': 3, 'pattern': r'(?:\d{5})\s(.*)', 'optional': False},
        'postal_code': {'line': 3, 'pattern': r'(\d{5})(?:.*)', 'optional': False},
        'from': {'line': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'optional': True},
        'purpose': {'line': 0, 'pattern': r'(Abholung|Zustellung)', 'optional': False},
        'timestamp': {'line': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'optional': False},
        'until': {'line': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'optional': True}
    },
    'header': {
        'id': {'line': 0, 'pattern': r'.*(\d{10})', 'optional': True},
        'cash_payment': {'line': 0, 'pattern': '(BAR)', 'optional': True}
    },
    'client': {
        'client_id': {'line': 0, 'pattern': r'.*(\d{5})$', 'optional': False},
        'client_name': {'line': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'optional': False}
    },
    'itinerary': {
        'km': {'line': 0, 'pattern': r'(\d{1,2},\d{3})\skm', 'optional': True}
    }
}

def _print_debug_message(name, item, contents):
    """
    Print a debug message showing exactly where the scraping went wrong.

    :param name: (str) the name of the field
    :param item: (dict) the field information
    :param item: (list) the section of the document
    """
    print('**************************************************')
    print('Could not scrape \'{}\' from \'{}\' on line {}\n'.format(
        name,
        contents[item['line']],
        item['line'])
    )
    for line, content in enumerate(contents):
        print(line, ': ', content)
    print('**************************************************\n')

def _scrape_subset(fields, soup_subset):
    """
    Scrape a sub-section of the html document. The document format very is unreliable:
    the number of lines in each section varies and the number of fields on each line
    also varies! For this reason, our scraping strategy is... well... conservative.
    The motto is: one field at a time! The goal is to end up with a robust set of data.
    Failure to collect information is not a show-stopper but we should know about it!

    :param fields: (dict) the fields to be collected
    :param soup_subset: (tag object) cleaned up html
    :return: (dict) field name/value pairs
    """
    contents = list(soup_subset.stripped_strings)

    collected = dict()
    for name, item in fields.items():
        match = re.match(item['pattern'], contents[item['line']])
        if match:
            collected[name] = match.group(1)
        else:
            if item['optional']:
                collected[name] = None
            else:
                _print_debug_message(name, item, contents)

    return collected

def scrape_job(soup):
    """
    Scrape the shit out of the html document using BeautifulSoup and a little regex.
    Job details are returned as a dictionary and addresses as a list of dictionaries.
    Each dictionary contains field name/value pairs. All values are raw strings.

    :param soup: (tag object) cleaned up html produced by BeautifulSoup
    :return: (tuple) details, addresses
    """
    details = dict()

    # Scrape various sections in the document
    subsets = ['header', 'client', 'itinerary']
    for subset in subsets:
        soup_subset = soup.find_next(name=TAGS[subset]['name'])
        fields_subset = _scrape_subset(BLUEPRINTS[subset], soup_subset)
        details.update(fields_subset)

    # Scrape prices at the bottom of the page
    soup_subset = soup.find(TAGS['prices']['name'])
    prices = _scrape_prices(soup_subset)
    details.update(prices)

    # Scrape an arbitrary number of addresses
    soup_subsets = soup.find_all(name=TAGS['address']['name'], attrs=TAGS['address']['attrs'])
    addresses = list()
    for soup_subset in soup_subsets:
        address = _scrape_subset(BLUEPRINTS['address'], soup_subset)
        addresses.append(address)

    return details, addresses

def _scrape_prices(soup_subset):
    """
    Scrape off the 'prices' table at the bottom of the page.
    This section is scraped seperately because it's already
    formatted as a table.

    :param soup_subset: (tag object) cleaned up html
    :return: (dict) field name/value pairs
    """
    # The table is grabbed as a one-dimensional list
    # of cells but we want it in dictionary format.
    cells = list(soup_subset.stripped_strings)
    prices_table = dict(zip(cells[::2], cells[1::2]))

    # Original field names are no good. Change them.
    # Note: there are several flavours of overnights.
    keys = [
        ('Stadtkurier',         'city_tour'),
        ('Stadt Stopp(s)',      'extra_stops'),
        ('OV Ex Nat PU',        'overnight'),
        ('ON Ex Nat Del.',      'overnight'),  # TODO Keep my eyes open for more OV flavours
        ('EmpfangsbestÃ¤t.',    'fax_confirm'),
        ('Wartezeit min.',      'waiting_time')
    ]
    for old, new in keys:
        if old in prices_table:
            prices_table[new] = prices_table.pop(old)

    # This field contains the waiting time in minutes
    # as well as the price. We just want the price.
    if 'waiting_time' in prices_table.keys():
        prices_table['waiting_time'] = prices_table['waiting_time'][7::]

    return prices_table

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
    pp = pprint.PrettyPrinter()
    for filename in filenames:
        with open(filename) as file_handle:
            soup = BeautifulSoup(file_handle).find(id='order_detail')  # TODO Fix Unicode problem
            data = scrape_job(soup)
            print(filename)
            pp.pprint(data[0])
            pp.pprint(data[1])
            print()
main()