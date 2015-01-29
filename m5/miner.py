""" Miner classes and related stuff. """

import re
from bs4 import BeautifulSoup
import subprocess


class MessengerMiner:
    """ The MessengerMiner class handles scraping off data from the Messenger server. """

    _DEBUG = True

    # Where the information hides on a job's web page
    _TAGS = dict(
        address={'name': 'div', 'attrs': {'data-collapsed': 'true'}},
        header={'name': 'h2', 'attrs': None},
        client={'name': 'h4', 'attrs': None},
        itinerary={'name': 'p', 'attrs': None},
        prices={'name': 'tbody', 'attrs': None}
    )

    # Each field has a regex blueprint.
    _BLUEPRINTS = dict(
        address=dict(
            company={'line': 1, 'pattern': r'(.*)', 'optional': False},
            address={'line': 2, 'pattern': r'(.*)', 'optional': False},
            city={'line': 3, 'pattern': r'(?:\d{5})\s(.*)', 'optional': False},
            postal_code={'line': 3, 'pattern': r'(\d{5})(?:.*)', 'optional': False},
            after={'line': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'optional': True},
            purpose={'line': 0, 'pattern': r'(Abholung|Zustellung)', 'optional': False},
            timestamp={'line': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'optional': False},
            until={'line': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'optasty_souptional': True}
        ),
        header=dict(
            job_id={'line': 0, 'pattern': r'.*(\d{10})', 'optional': True},
            cash_payment={'line': 0, 'pattern': '(BAR)', 'optional': True}
        ),
        client=dict(
            client_id={'line': 0, 'pattern': r'.*(\d{5})$', 'optional': False},
            client_name={'line': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'optional': False}
        ),
        itinerary=dict(
            km={'line': 0, 'pattern': r'(\d{1,2},\d{3})\skm', 'optional': True}
        )
    )

    def __init__(self, date, session, server):
        """ Initialize class attributes.

        :param date: the datetime object to be mined
        :param session: the current session object
        :param server: the server url
        """
        self.date = date
        self._sdate = date.strftime('%d-%m-%Y')
        self._session = session
        self._server = server
        self.debug_messages = []
        self.raw_data = None

    def fetch_jobs(self) -> set:
        """
        Return unique 'uuid' request parameters for every job on that day.

        :return: A set of 'uuid' strings
        """

        # Prepare the request and shoot
        url = self._server + 'll.php5'
        payload = {'status': 'delivered', 'datum': self.date.strftime('%d.%m.%Y')}
        response = self._session.get(url, params=payload)

        # Scrape the uuid parameters
        pattern = 'uuid=(\d{7})'
        jobs = re.findall(pattern, response.text)

        if self._DEBUG:
            soup = BeautifulSoup(response.text)
            self._save_html(soup, 'soup', is_soup=True)
            self._save_html(response.text, 'raw', is_soup=False)

        # Each uuid appears twice on the page
        # (two links), so dump the duplicates.
        return set(jobs)

    def get_job(self, uuid) -> object:
        """
        Browse the web page for that day and return a beautiful soup.

        :param uuid: the job's uuid string request parameter
        :return: cleaned up html as produced by bs4
        """

        # Prepare the request and shoot
        url = self._server + 'll_detail.php5'
        payload = {'status': 'delivered', 'uuid': uuid}
        response = self._session.get(url, params=payload)

        # Turn it into a digestible soup
        # and filter out the tasty stuff
        soup = BeautifulSoup(response.text)
        # order_detail = soup.find(id='order_detail')

        if self._DEBUG:
            self._save_html(soup, uuid)

        # assert isinstance(order_detail, object)
        return soup

    def _save_html(self, source, stamp, is_soup=True) -> str:
        """
        From the soup, prettify the html and save it to file.

        :param source: (tag object) the web page in soup form
        :param stamp: (str) the job's identifier
        """

        if is_soup:
            text = source.prettify()
        else:
            text = source

        path = 'output/' + self._sdate + '-' + stamp + '.html'
        with open(path, 'w') as f:
            f.write(text)
            f.close()

        return path

    def _scrape_subset(self, blueprint, soup_subset) -> dict:
        """
        Scrape a sub-section of the html document using the blueprints.

        :param blueprint: (dict) how to scrape each field
        :param soup_subset: (tag object) the text inside an html tag in soup form
        :return: field name/value pairs
        """

        # The document format very is unreliable: the number of lines
        # in each section varies and the number of fields on each line
        # also varies. For this reason, our scraping is conservative.
        # The motto is: one field at a time! The goal is to end up with
        # a robust set of data. Failure to collect information is not a
        # show-stopper but we should know about it!

        # Split the inner contents of the html tag into a list of lines
        contents = list(soup_subset.stripped_strings)

        collected = dict()

        # Collect each field one by one, even if that
        # means returning to the same line several times.
        for name, field in blueprint.items():
            match = re.match(field['pattern'], contents[field['line']])
            if match:
                collected[name] = match.group(1)
            else:
                if field['optional']:
                    # If we fail to scrape the field but the field is optional:
                    # assign the dictionary key anyways:
                    collected[name] = None
                else:
                    # TODO Raise a warning when a non-optional field is not found
                    # If we fail to scrape a field that we actually need: ouch!
                    # Don't assign any key and make sure we give some feedback.
                    self._store_debug_message(name, field, contents)

        return collected

    def scrape_job(self, soup) -> dict:
        """
        Scrape out of a job's web page using BeautifulSoup and a little regex.
        Job details and prices are returned as dictionaries, addresses as a list
        of dictionaries. Values are returned as raw strings.

        :param soup: (tag object) the job's web page in soup form
        :return: details, prices, addresses
        """

        # Step 1: job details
        details = dict()

        subsets = ['header', 'client', 'itinerary']

        for subset in subsets:
            soup_subset = soup.find_next(name=self._TAGS[subset]['name'])
            fields_subset = self._scrape_subset(self._BLUEPRINTS[subset], soup_subset)
            details.update(fields_subset)

        # Step 2: the price table at the bottom of the page
        soup_subset = soup.find(self._TAGS['prices']['name'])
        prices = self._scrape_prices(soup_subset)

        # Step 3: an arbitrary number of addresses
        soup_subsets = soup.find_all(
            name=self._TAGS['address']['name'],
            attrs=self._TAGS['address']['attrs']
        )

        addresses = list()
        for soup_subset in soup_subsets:
            address = self._scrape_subset(self._BLUEPRINTS['address'], soup_subset)
            addresses.append(address)

        # Package everything up nicely
        raw_data = dict(details=details, prices=prices, addresses=addresses)

        return raw_data

    @staticmethod
    def _scrape_prices(soup_subset) -> dict:
        """
        Scrape the 'prices' table at the bottom of the page. This section is
        scraped seperately because it's already neatly formatted as a table.

        :param soup_subset: (tag object) cleaned up html
        :return: field name/value pairs
        """

        # The table is scraped as a one-dimensional list
        # of cells but we want it in dictionary format.
        cells = list(soup_subset.stripped_strings)
        price_table = dict(zip(cells[::2], cells[1::2]))

        # Original field names are no good. Change them.
        # Note: there are several flavours of overnights.
        keys = [
            ('Stadtkurier',         'city_tour'),
            ('Stadt Stopp(s)',      'extra_stops'),
            ('OV Ex Nat PU',        'overnight'),
            ('ON Ex Nat Del.',      'overnight'),
            ('EmpfangsbestÃ¤t.',    'fax_confirm'),
            ('Wartezeit min.',      'waiting_time')
        ]

        for old, new in keys:
            if old in price_table:
                price_table[new] = price_table.pop(old)

        # The waiting time cell has the time in minutes
        # as well as the price. We just want the price.
        if 'waiting_time' in price_table.keys():
            price_table['waiting_time'] = price_table['waiting_time'][7::]

        return price_table

    def package_job(self, raw_data):
        # TODO Data pre-processing goes here!
        self.raw_data = raw_data

    def _store_debug_message(self, name: str, item, contents):
        """
        Save a debug message showing the context where the scraping went wrong.
        And while we're at it, save a copy of the html file for later inspection.

        :param name: (str) the name of the field
        :param item: (dict) the field information
        :param item: (list) the section of the document
        """

        seperator = '*' * 50
        self.debug_messages.append(seperator)
        self.debug_messages.append('Could not scrape \'{}\' from \'{}\' on line {}\n'.format(
            name,
            contents[item['line']],
            item['line'])
        )
        for line, content in enumerate(contents):
            self.debug_messages.append(str(line) + ': ' + content)
        self.debug_messages.append(seperator)
