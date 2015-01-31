""" Miner classes and related stuff. """

import re

from datetime import datetime
from requests import Session
from bs4 import BeautifulSoup
from pprint import PrettyPrinter

from m5.utilities import notify, log_me, time_me


class Miner:
    """
    The 'mine' method scrapes off data from the company server.
    It's the only public method in the class. Everything else
    is low-level internals.
    """

    _DEBUG = True

    # Some tags are a target.
    _TAGS = dict(header={'name': 'h2', 'attrs': None},
                 client={'name': 'h4', 'attrs': None},
                 itinerary={'name': 'p', 'attrs': None},
                 prices={'name': 'tbody', 'attrs': None},
                 address={'name': 'div', 'attrs': {'data-collapsed': 'true'}})

    # Each field has a regex instructions.
    _BLUEPRINTS = {'itinerary': dict(km={'line_number': 0, 'pattern': r'(\d{1,2},\d{3})\skm', 'optional': True}),
                   'header': dict(job_id={'line_number': 0, 'pattern': r'.*(\d{10})', 'optional': True},
                                  cash_payment={'line_number': 0, 'pattern': '(BAR)', 'optional': True}),
                   'client': dict(client_id={'line_number': 0, 'pattern': r'.*(\d{5})$', 'optional': False},
                                  client_name={'line_number': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'optional': False}),
                   'adddress': dict(company={'line_number': 1, 'pattern': r'(.*)', 'optional': False},
                                    address={'line_number': 2, 'pattern': r'(.*)', 'optional': False},
                                    city={'line_number': 3, 'pattern': r'(?:\d{5})\s(.*)', 'optional': False},
                                    postal_code={'line_number': 3, 'pattern': r'(\d{5})(?:.*)', 'optional': False},
                                    after={'line_number': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'optional': True},
                                    purpose={'line_number': 0, 'pattern': r'(Abholung|Zustellung)', 'optional': False},
                                    timestamp={'line_number': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'optional': False},
                                    until={'line_number': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'optional': True}))

    def __init__(self, dates: set, server: str, session: Session):
        """
        Instantiate a Miner object for a set of dates.

        :param dates: a set of datetime objects
        :param server: the url of the server
        :param session: the current
        """

        self.dates = dates
        self._server = server
        self._session = session

        # Currently mining the
        # following date and job number
        self._date = datetime(1, 1, 1)
        self._uuid = str()

    @time_me
    @log_me
    def mine(self) -> list:
        """ Mine a set of dates from the server.
        :return: a list of (jobs, addresses) tuples
        """

        jobs = list()
        pp = PrettyPrinter()

        for date in self.dates:
            self._date = date

            # Go browse the summary page for that day
            # and scrape off uuid parameters.
            uuids = self.scrape_uuids(date)

            # Was it a working day?
            if uuids:
                for uuid in uuids:
                    self._uuid = uuid

                    soup = self._get_job(uuid)
                    job = self._scrape(soup)

                    if self._DEBUG:
                        pp.pprint(job)

                    jobs.append(jobs)

                notify('Mined {} OK.', date.strftime('%d-%m-%Y'))

        return jobs

    @log_me
    def process(self, jobs: list) -> list:
        """
        Scraped data fields are returned as raw strings by the miner.
        This is where the data gets processed before it can be stored to
        the database.
        Unserialize the fields, geocode each address and return a table
        of checkpoints (with possible duplicates) and a table of checkins.

        """

        pass

    def scrape_uuids(self, date: datetime) -> set:
        """
        Return unique uuid request parameters for each
        job by scraping the overview page for that date.

        :param date: a single day
        :return: A set of uuid strings
        """

        url = self._server + 'll.php5'
        payload = {'status': 'delivered',
                   'datum': date.strftime('%d.%m.%Y')}

        response = self._session.get(url, params=payload)

        pattern = 'uuid=(\d{7})'
        jobs = re.findall(pattern, response.text)

        # Each uuid string appears twice: dump the duplicates.
        return set(jobs)

    def _get_job(self, uuid: str) -> BeautifulSoup:
        """ Get the page for that date and return a soup.

        :param uuid: the uuid request parameter
        :return: parsed html soup
        """

        url = self._server + 'll_detail.php5'
        payload = {'status': 'delivered', 'uuid': uuid}

        response = self._session.get(url, params=payload)

        # Parse the raw html text...
        soup = BeautifulSoup(response.text)
        # ...and keep only what we need.
        job = soup.find(id='order_detail')

        return job

    def _scrape_fragment(self, blueprint: dict, soup_fragment: BeautifulSoup) -> dict:
        """ Scrape a fragment of the page. In goes the blueprint, out comes a dictionnary.

        :param blueprint: the instructions
        :param soup_fragment: a parsed html fragment
        :return: field name/value pairs
        """

        # The document format very is unreliable: the number of lines
        # in each section varies and the number of fields on each line
        # also varies. For this reason, our scraping is conservative.
        # The motto is: one field at a time! The goal is to end up with
        # a robust set of data. Failure to collect information is not a
        # show-stopper but we should know about it!

        # Split the inner contents of the html tag into a list of lines
        contents = list(soup_fragment.stripped_strings)

        collected = dict()

        # Collect each field one by one, even if that
        # means returning to the same line several times.
        for field_name, field in blueprint.items():
            match = re.match(field['pattern'], contents[field['line_number']])
            if match:
                collected[field_name] = match.group(1)
            else:
                if field['optional']:
                    # If we fail to scrape the field but the field is optional:
                    # assign the dictionary key anyways:
                    collected[field_name] = None
                else:
                    # If we fail to scrape a field that we actually need: ouch!
                    # Don't assign any key and make sure we give some feedback.
                    message = 'Failed to scrape {}: {}ll_detail.php5?status=delivered&uuid={}'
                    notify(message,
                           field_name,
                           self._server,
                           self._uuid)

        return collected

    def _scrape(self, soup: BeautifulSoup) -> tuple:
        """
        Scrape out of a job's web page using bs4 and re modules.
        In comes the soup, out go field name/value pairs as raw strings.

        :param soup: the job's web page
        :return: job_details and addresses as a tuple
        """

        # Step 1: scrape job details
        job_details = dict()

        # Step 1.1: everything except prices
        fragments = ['header', 'client', 'itinerary']
        # TODO Generate blueprints on the fly

        for fragment in fragments:
            soup_fragment = soup.find_next(name=self._TAGS[fragment]['name'])
            fields_subset = self._scrape_fragment(self._BLUEPRINTS[fragment],
                                                  soup_fragment)
            job_details.update(fields_subset)

        # Step 1.2: the price table
        soup_fragment = soup.find(self._TAGS['prices']['name'])
        prices = self._scrape_prices(soup_fragment)

        job_details.update(prices)

        # Step 2: scrape an arbitrary number of addresses
        soup_fragments = soup.find_all(name=self._TAGS['address']['name'],
                                       attrs=self._TAGS['address']['attrs'])
        addresses = list()
        for soup_fragment in soup_fragments:
            address = self._scrape_fragment(self._BLUEPRINTS['address'], soup_fragment)

            addresses.append(address)

        job = job_details, addresses
        return job

    @staticmethod
    def _scrape_prices(soup_fragment: BeautifulSoup) -> dict:
        """
        Scrape the 'prices' table at the bottom of the page. This section is
        scraped seperately because it's already neatly formatted as a table.

        :param soup_fragment: parsed html
        :return: item/price pairs
        """

        # The table is scraped as a one-dimensional list
        # of cells but we want it in dictionary format.
        cells = list(soup_fragment.stripped_strings)
        price_table = dict(zip(cells[::2], cells[1::2]))

        # Original field names are no good. Change them.
        keys = [('Stadtkurier', 'city_tour'),
                ('Stadt Stopp(s)', 'extra_stops'),
                ('OV Ex Nat PU', 'overnight'),
                ('ON Ex Nat Del.', 'overnight'),
                ('EmpfangsbestÃ¤t.', 'fax_confirm'),
                ('Wartezeit min.', 'waiting_time')]

        for old, new in keys:
            if old in price_table:
                price_table[new] = price_table.pop(old)

        # The waiting time cell has the time in minutes
        # as well as the price. We just want the price.
        if 'waiting_time' in price_table.keys():
            price_table['waiting_time'] = \
                price_table['waiting_time'][7::]

        return price_table

