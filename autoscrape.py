from bs4 import BeautifulSoup
import re


def section_blueprints():
    """
    Define the blueprints for the section scraper. Each blueprint is keyed
    by the html tag that it targets and contains information about:
        - which lines to scrape
        - what fields to look for in each line
        - what regex pattern to run on each line

    :return: (dict) A dictionary of blueprints
    """
    blueprint = dict()
    # General information
    blueprint['h2'] = {'lines': [0],
                       'patterns': [r'(?:BAR\s)?(\d{10})'],
                       'fields': [['id']]
                       }
    # Client information
    blueprint['h4'] = {'lines': [0],
                       'patterns': [r'Kunde:\s(.*)\s\|\s(\d{5})'],
                       'fields': [['client_name', 'client_number']]
                       }
    return blueprint

def main():
    file = open('19.12.2014-2976786.html')
    html_source = BeautifulSoup(file).find(id='order_detail')
    fields = dict()

    # Scrape the prices at the bottom of the page
    prices = scrape_prices(html_source)
    fields.update(prices)

    # Scrape multiple subsections
    # of the page using our blueprints
    sections = section_blueprints()
    for tag, section in sections.items():
        html_subset = html_source.find(name=tag)
        miscellaneous = scrape_section(section, html_subset)

    fields.update(miscellaneous)
    print(fields)

def scrape_section(bp, source):
    """
    Scrape off a small section from the html document contained
    inside a tag. Done using BeautifulSoup and a little regex magic.

    :param bp: (dict) The section blueprint
    :param source: (str) cleaned up html produced by BeautifulSoup
    :return: (dict) field name/value pairs
    """
    strings = list(source.stripped_strings)
    section_fields = dict()

    for line in bp['lines']:
        match = re.match(bp['patterns'][line], strings[line])
        for index, name in enumerate(bp['fields'][line]):
            # Indices for matched groups start at 1
            section_fields[name] = match.group(index+1)

    return section_fields


def scrape_prices(source):
    """
    Scrape the 'prices' table at the bottom of the page. This section is
    scraped seperately precisely because it's formatted as a table.

    :param source: (str) cleaned up html produced by BeautifulSoup
    :return: (dict) field name/value pairs
    """
    # Grab the only html table in the document
    html_subset = source.find(name='tbody')
    lines = list(html_subset.stripped_strings)

    # The table is returned as a one-dimensional list
    # of strings but we want it in dictionary format.
    prices = dict(zip(lines[::2], lines[1::2]))

    # Original field names are no good. Change them.
    keys = [('Stadtkurier', 'city_tour'),
            ('Stadtstop(s)', 'extra_stops'),
            ('OV.', 'overnight'),
            ('EmpfangsbestÃ¤t.',  'fax_return'),
            ('Wartezeit min.',  'waiting_time')]
    for old, new in keys:
        if old in prices:
            prices[new] = prices.pop(old)

    return prices

main()