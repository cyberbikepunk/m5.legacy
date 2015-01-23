""" This submodule contains Miner classes and related stuff. """

import re
from bs4 import BeautifulSoup


class MessengerMiner:
    """ The MessengerMiner class handles scraping off data from the company server. """

    # BeautifulSoup4 helps us cut up web pages into small pieces.
    # Here are the pieces where the data hides.
    _TAGS = dict(
        address={'name': 'div', 'attrs': {'data-collapsed': 'true'}},
        header={'name': 'h2', 'attrs': None},
        client={'name': 'h4', 'attrs': {'style:': 'margin-bottom: 5px'}},
        itinerary={'name': 'p', 'attrs': {'style:': 'margin-top: 5px'}},
        prices={'name': 'tbody', 'attrs': None}
    )

    # Each field has a regex blueprint. Fields tagged 'optional' are
    # sometime on and sometimes not!
    _BLUEPRINTS = dict(
        address=dict(
            company={'line': 1, 'pattern': r'(.*)', 'optional': False},
            address={'line': 2, 'pattern': r'(.*)', 'optional': False},
            city={'line': 3, 'pattern': r'(?:\d{5})\s(.*)', 'optional': False},
            postal_code={'line': 3, 'pattern': r'(\d{5})(?:.*)', 'optional': False},
            after={'line': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'optional': True},
            purpose={'line': 0, 'pattern': r'(Abholung|Zustellung)', 'optional': False},
            timestamp={'line': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'optional': False},
            until={'line': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'optional': True}
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

        :param date: (datetime obj) the date to be mined
        :param session: (request.session obj) the current http session
        :param server: (str) the server url
        """
        self.date = date
        self._session = session
        self._server = server
        self.debug_messages = list()
        self.raw_data = None

    def fetch_jobs(self):
        """ Return a unique 'uuid' request parameter for every job on that day.
        :return: (set) A set of 'uuid' strings
        """

        # Prepare the request and shoot
        url = self._server + 'll.php5'
        payload = {'status': 'delivered', 'datum': self.date.strftime('%d.%m.%Y')}
        response = self._session.get(url, params=payload)

        # Scrape the uuid parameters
        pattern = 'uuid=(\d{7})'
        jobs = re.findall(pattern, response.text)

        # Each uuid appears twice on the page
        # (two links). Dump the duplicates.
        return set(jobs)

    def get_job(self, job):
        """ Browse the web page for that day and return a beautiful soup.

        :param job: (str) the job's uuid request parameter
        :return (tag object) cleaned up html as produced by bs4
        """

        # Prepare the request and shoot
        url = self._server + 'll_detail.php5'
        payload = {'status': 'delivered', 'uuid': job}
        response = self._session.get(url, params=payload)

        # Turn dirty html text into a digestible soup
        # then squeeze out the really tasty stuff
        soup = BeautifulSoup(response.text)
        return soup.find(id='order_detail')

    def _save_job(self, soup, uuid):
        """ From a soup, prettify the html and save it to file.

        :param soup: (tag object) the web page in soup form
        :param uuid: (str) the job's identifier
        """

        # TODO Current folder for now: user folders in the future
        f = self.date.strftime('%d.%m.%Y') + '-' + uuid + '.html'
        with open(f, 'w') as f:
            f.write(soup.prettify())
            f.close()

    def _scrape_subset(self, fields, soup_subset):
        """
        Scrape a sub-section of the html document. The document format very is unreliable:
        the number of lines in each section varies and the number of fields on each line
        also varies! For this reason, our scraping strategy is somewhat conservative.
        The motto is: one field at a time! The goal is to end up with a robust set of data.
        Failure to collect information is not a show-stopper but we should know about it!

        :param fields: (dict) the fields to be collected
        :param soup_subset: (tag object) the inner contents of a tag in soup form
        :return: (dict) field name/value pairs
        """

        # Split the inner contents of an html tag into a list of lines
        contents = list(soup_subset.stripped_strings)

        collected = dict()
        # Collect each field one by one, even if that
        # means returning to the same line several times.
        for name, item in fields.items():
            match = re.match(item['pattern'], contents[item['line']])
            if match:
                collected[name] = match.group(1)
            else:
                if item['optional']:
                    # We fail to scrape the field but it turns out
                    # to be optional: assign a dictionary key anyways!
                    collected[name] = None
                else:
                    # We fail to scrape a field but we actually need it... ouch!
                    # Don't assign any key and make sure we bubble up some feedback.
                    self._store_debug_message(name, item, contents)

        return collected

    def scrape_job(self, soup):
        """
        Scrape the shit out of a job's web page using BeautifulSoup and a little regex.
        In three steps: first the jobs details, then the price table and finally the addresses.
        Job details and prices are returned as dictionaries, addresses as a list of dictionaries.
        Each dictionary contains scraped field name/value pairs. Values are returned as raw strings.

        :param soup: (tag object) the job's web page in soup form
        :return details, prices, addresses
        :rtype tuple
        """

        # STEP 1/3: scrape job details one section at a time
        details = dict()
        subsets = ['header', 'client', 'itinerary']

        for subset in subsets:
            soup_subset = soup.find_next(name=self._TAGS[subset]['name'])
            fields_subset = self._scrape_subset(self._BLUEPRINTS[subset], soup_subset)

            # Put all collected fields in the same basket
            details.update(fields_subset)

        # STEP 2/3: scrape the price table at the bottom of the page
        soup_subset = soup.find(self._TAGS['prices']['name'])
        prices = self._scrape_prices(soup_subset)

        # STEP 3/3: scrape an arbitrary number of addresses
        # Like I sai
        name = self._TAGS['address']['name']
        attrs = self._TAGS['address']['attrs']
        soup_subsets = soup.find_all(name=name, attrs=attrs)

        addresses = list()
        for soup_subset in soup_subsets:
            address = self._scrape_subset(self._BLUEPRINTS['address'], soup_subset)
            addresses.append(address)

        # Package the whole thing up nicely inside a tuple
        raw_data = details, prices, addresses
        return raw_data

    def _scrape_prices(self, soup_subset):
        """
        Scrape off the 'prices' table at the bottom of the page. This section
        is scraped seperately because it's already neatly formatted as a table.

        :param soup_subset: (tag object) cleaned up html
        :return: (dict) field name/value pairs
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
        """ Pre-process and package up the data intelligently """
        # TODO Raw data pre-processing goes here!
        self.raw_data = raw_data

    def _store_debug_message(self, name: str, item, contents):
        """ Save a debug message showing the context in which the scraping went wrong.

        :param name: (str) the name of the field
        :param item: (dict) the field information
        :param item: (list) the section of the document
        """
        self.debug_messages.append('************************************************')
        self.debug_messages.append('Could not scrape \'{}\' from \'{}\' on line {}\n'.format(
            name,
            contents[item['line']],
            item['line'])
        )
        for line, content in enumerate(contents):
            self.debug_messages.append(str(line) + ': ' + content)
        self.debug_messages.append('************************************************')
