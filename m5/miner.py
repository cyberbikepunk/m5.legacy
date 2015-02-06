""" Miner classes and related stuff. """

import inspect
from time import strptime
from os.path import isfile

import re
import sys

from datetime import datetime
from requests import Session
from bs4 import BeautifulSoup
from pprint import PrettyPrinter

from m5.utilities import geocode, notify, log_me, time_me
from m5.model import Checkin, Checkpoint, Client, Order
import m5.model

def null_or(int, param):
    pass


class Miner:
    """
    The 'mine' method scrapes off data from the company server. It's the
    only public method in the class. Everything else is low-level internals.
    """

    _DEBUG = True

    # Some tags are a target.
    _TAGS = dict(header={'name': 'h2', 'attrs': None},
                 client={'name': 'h4', 'attrs': None},
                 itinerary={'name': 'p', 'attrs': None},
                 prices={'name': 'tbody', 'attrs': None},
                 address={'name': 'div', 'attrs': {'data-collapsed': 'true'}})

    # Each field has a regex instructions.
    _BLUEPRINTS = {'itinerary': dict(distance={'line_nb': 0, 'pattern': r'(\d{1,2},\d{3})\sdistance', 'optional': True}),
                   'header': dict(order_id={'line_nb': 0, 'pattern': r'.*(\d{10})', 'optional': True},
                                  is_payed_cash={'line_nb': 0, 'pattern': r'(BAR)', 'optional': True}),
                   'client': dict(client_id={'line_nb': 0, 'pattern': r'.*(\d{5})$', 'optional': False},
                                  client_name={'line_nb': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'optional': False}),
                   'adddress': dict(company={'line_nb': 1, 'pattern': r'(.*)', 'optional': False},
                                    address={'line_nb': 2, 'pattern': r'(.*)', 'optional': False},
                                    city={'line_nb': 3, 'pattern': r'(?:\d{5})\s(.*)', 'optional': False},
                                    postal_code={'line_nb': 3, 'pattern': r'(\d{5})(?:.*)', 'optional': False},
                                    after={'line_nb': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'optional': True},
                                    purpose={'line_nb': 0, 'pattern': r'(Abholung|Zustellung)', 'optional': False},
                                    timestamp={'line_nb': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'optional': False},
                                    until={'line_nb': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'optional': True})}

    @staticmethod
    def build_blueprints():
        classes = sys.modules[model]

        for name, obj in inspect.getmembers(sys.modules[__name__]):
            if inspect.isclass(obj):
                print obj

    def __init__(self, user: str, date: datetime, server: str, session: Session):
        """
        Instantiate a Miner object for a given user and date.

        :param user: the current user
        :param date: a datetime object
        :param server: the url of the server
        :param session: the current
        """

        self.date = date
        self.server = server
        self.session = session
        self.user = user

    def filename(self, uuid):
        """ Construct a filename from a job uuid """
        return '%s_%s.html' % (self.date.strftime('%Y-%m-%d'), uuid)

    @time_me
    @log_me
    def mine(self) -> list:
        """ Mine a given date from the server.
        :return: a list of (job_details, addresses) tuples
        """

        jobs = list()
        pp = PrettyPrinter()

        # Go browse the summary page for that day
        # and scrape off uuid parameters.
        uuids = self.scrape_uuids(self.date)

        # Was it a working day?
        if uuids:
            for uuid in uuids:
                if self.is_cached(uuid):
                    soup = self.load_job(uuid)
                else:
                    soup = self._get_job(uuid)

                job_details, addresses = self._scrape(soup)

                if self._DEBUG:
                    pp.pprint(job_details)

                jobs.append((job_details, addresses))
                notify('Mined {} OK.', self.date.strftime('%d-%m-%Y'))

        return jobs

    def process(self, raw_data: list):
        """ Process the raw data and return declarative objects.

        :param raw_data: a list of tuples (job_details, addresses)
        :return: instances of Client, Order, Checkin and Checkpoint classes
        """

        orders = list()
        clients = list()
        checkpoints = list()
        checkins = list()

        for raw_datum in raw_data:
            job_details = raw_datum[0]
            addresses = raw_datum[1]

            client = Client(**{'client_id': null_or(int, (job_details['client_id'])),
                               'order_id': null_or(int, (job_details['order_id'])),
                               'client_name': int(job_details['client_name'])})

            order = Order(**{'order_id': int(job_details['order_id']),
                             'date': self.date,
                             'distance': int(job_details['distance']),
                             'is_payed_cash': (bool(job_details['is_payed_cash'])),
                             'city_tour': float(job_details['city_tour']),
                             'extra_stops': float(job_details['extra_stops']),
                             'overnight': float(job_details['overnight']),
                             'fax_confirm': float(job_details['fax_confirm']),
                             'waiting_time': float(job_details['waiting_time'])})

            clients.append(client)
            orders.append(order)

            for address in addresses:
                geocoded = geocode(address)

                checkpoint = Checkpoint(**{'checkpoint_id': geocoded['serial'],
                                           'street_name': geocoded['street_name'],
                                           'street_nb': geocoded['street_nb'],
                                           'city': geocoded['city'],
                                           'postal_code': int(geocoded['postal_code']),
                                           'company': address['company']})

                checkin = Checkin(**{'checkin_id': strptime(address['until'], '%H:%M'),
                                     'order_id': int(job_details['order_id']),
                                     'checkpoint_id': geocoded['serial'],
                                     'purpose': 'pickup' if address['purpose'] else 'dropoff',
                                     'after': strptime(address['after'], '%H:%M') if address['after'] else ,
                                     'until': strptime(address['until'], '%H:%M')})

                checkpoints.append(checkpoint)
                checkins.append(checkin)

        return clients, orders, checkpoints, checkins

    def scrape_uuids(self, date: datetime) -> set:
        """
        Return unique uuid request parameters for each
        job by scraping the overview page for that date.

        :param date: a single day
        :return: A set of uuid strings
        """

        url = self.server + 'll.php5'
        payload = {'status': 'delivered',
                   'datum': date.strftime('%d.%m.%Y')}

        response = self.session.get(url, params=payload)

        pattern = 'uuid=(\d{7})'
        jobs = re.findall(pattern, response.text)

        # Each uuid string appears twice: dump the duplicates.
        return set(jobs)

    def _get_job(self, uuid: str) -> BeautifulSoup:
        """ Get the page for that date and return a soup.

        :param uuid: the uuid request parameter
        :return: parsed html soup
        """

        url = self.server + 'll_detail.php5'
        payload = {'status': 'delivered', 'uuid': uuid}

        response = self.session.get(url, params=payload)

        # Parse the raw html text...
        soup = BeautifulSoup(response.text)
        # ... save the file for future reference...
        self._save_job(soup, uuid)
        # ...and send back only what we need.
        job = soup.find(id='order_detail')

        return job

    def _scrape_fragment(self, blueprint: dict, soup_fragment: BeautifulSoup, uuid) -> dict:
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
            match = re.match(field['pattern'], contents[field['line_nb']])
            if match:
                collected[field_name] = match.group(1)
            else:
                if field['optional']:
                    # If we fail to scrape the field but the field is optional:
                    # assign an empty string:
                    collected[field_name] = str()
                else:
                    # If we fail to scrape a field that we actually need, assign None.
                    # The database won't accept it because the fields is not nullable.
                    message = 'Failed to scrape {}: {}ll_detail.php5?status=delivered&uuid={}'
                    notify(message,
                           field_name,
                           self.server,
                           self.uuid)

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

        return job_details, addresses

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

    def is_cached(self, uuid):
        """ True if the current date been already downloaded. """

        if isfile(self.filename(uuid)):
            return True
        else:
            return False

    def load_job(self, uuid):
        """ Load a cached file. """

        with open(self.filename(uuid), 'w+') as f:
            pretty_html = f.read()
            f.close()
        return BeautifulSoup(pretty_html)

    def _save_job(self, job: BeautifulSoup, uuid):
        """
        Prettify the html for that date and save it to file.

        :param job: the html soup for a given date
        """

        pretty_html = job.prettify()

        with open(self.filename(uuid), 'w+') as f:
            f.write(pretty_html)
            f.close()

        notify('File {} saved.', self.filename)