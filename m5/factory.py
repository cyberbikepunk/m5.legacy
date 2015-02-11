""" Downloader, Scraper and Packager classes. """
from os import path

from geopy.exc import GeocoderTimedOut
from os.path import isfile
from geopy import Nominatim
from datetime import datetime, date
from time import strptime
from requests import Session
from bs4 import BeautifulSoup
from pprint import PrettyPrinter
from re import findall, match
from collections import namedtuple

from m5.utilities import notify, log_me, time_me, Stamped, Stamp, DEBUG
from m5.model import Checkin, Checkpoint, Client, Order


# TODO Refactor this module DRY.
#   - blueprints (scraping specifications) should be defined
#     within the db declarative model and unwrapped on the fly.
#   - the geo-coding and unserialisation procedures should
#     also be defined in the model and all dirty fixes removed.


class Downloader():

    def __init__(self, session: Session, directory: str, overwrite: bool=False):
        """ Instantiate a re-useable Downloader object.

        :param directory: absolute path to download directory
        :param overwrite: force file overwrite
        :param session: the current remote session
        """

        self._session = session
        self.directory = directory
        self.overwrite = overwrite

        # The base url for all requests:
        self.url = 'http://bamboo-mec.de/ll_detail.php5'

    @log_me
    def download(self, day: date=None) -> list:
        """
        Download the web-page showing one day of messenger data from the server,
        then save the raw html files and and return a list of beautiful soups.
        If that day has already been cached, serve the soup from the local file.

        :return: a list of Stamped(Stamp, BeautifulSoup) objects
        """

        if day is None:
            day = date.today()

        # Go browse the web-page for that day
        # and scrape off uuid(ish) parameters.
        uuids = self._scrape_uuids(day)

        soups = list()

        if not uuids:
            if DEBUG:
                soups = None
                notify('No jobs on {}.', str(day))

        else:
            for i, uuid in enumerate(uuids):
                stamp = Stamp(day, uuid)

                if self._is_cached(stamp) and not self.overwrite:
                    soup = self._load_job(stamp)
                    verb = 'Loaded'
                else:
                    soup = self._get_job(stamp)
                    verb = 'Downloaded'

                if DEBUG:
                    notify('{} {}/{} for {} {}.', verb, i+1, len(uuids), str(day), uuid)

                soups.append(Stamped(stamp, soup))

        return soups

    def _scrape_uuids(self, day: date) -> set:
        """
        Return unique uuid request parameters for each
        job by scraping the overview page for that date.

        :param day: a single day
        :return: A set of uuid strings
        """

        url = 'http://bamboo-mec.de/ll.php5'
        payload = {'status': 'delivered', 'datum': day.strftime('%d.%m.%Y')}
        response = self._session.get(url, params=payload)

        # The so called uuids are
        # actually 7 digit numbers.
        pattern = 'uuid=(\d{7})'

        jobs = findall(pattern, response.text)

        # Dump the duplicates.
        return set(jobs)

    def _get_job(self, stamp: Stamp) -> BeautifulSoup:
        """ Browse the web-page for that day and return a beautiful soup.

        :param stamp: the job Stamp tuple (date, uuid)
        :return: html as a beautiful soup object
        """

        payload = {'status': 'delivered',
                   'uuid': stamp.uuid,
                   'datum': stamp.date.strftime('%d.%m.%Y')}

        response = self._session.get(self.url, params=payload)

        soup = BeautifulSoup(response.text)
        self._save_job(stamp, soup)

        return soup

    def _filepath(self, stamp: Stamp):
        """ Where a job's downloaded html file is saved. """
        filename = '%s-uuid-%s.html' % (stamp.date.strftime('%Y-%m-%d'), stamp.uuid)
        return path.join(self.directory, filename)

    def _job_url(self, stamp: Stamp):
        """ The url of the web-page for a job. """
        return '{}?status=delivered&uuid={}&datum={}'.format(self.url,
                                                             stamp.uuid,
                                                             stamp.date.strftime('%d.%m.%Y'))

    def _is_cached(self, stamp: namedtuple):
        """ True if that job already has a local file. """
        if isfile(self._filepath(stamp)):
            return True
        else:
            return False

    def _save_job(self, stamp: namedtuple, soup: BeautifulSoup):
        """ Prettify the html for that date and save it to file. """
        pretty_html = soup.prettify()
        with open(self._filepath(stamp), 'w+') as f:
            f.write(pretty_html)
            f.close()

    def _load_job(self, stamp: namedtuple):
        """ Load a file from cache and return a beautiful soup. """
        with open(self._filepath(stamp), 'r') as f:
            html = f.read()
            f.close()
        return BeautifulSoup(html)


class Packager():
    """ The Packager class processes the raw serial data produced by the Scraper. """

    def __init__(self):
        pass

    def package(self, serial_items: list) -> list:
        """
        In goes serial data (raw strings) as returned by the Scraper. Out comes
        unserialized & packaged ORM table row objects digestable by the database.

        :param serial_items: a list of Stamped tuples (Stamp, serial_data)
        :return: a 4-tuple of lists (clients, orders, checkpoints, checkins)
        """

        clients = list()
        orders = list()
        checkpoints = list()
        checkins = list()

        for serial_item in serial_items:

            # Unpack the data
            day = serial_item[0][0]
            uuid = serial_item[0][1]
            job_details = serial_item[1][0]
            addresses = serial_item[1][1]

            client = Client(**{'client_id': self._unserialise(int, job_details['client_id']),
                               'name': self._unserialise(str, job_details['client_name'])})

            order = Order(**{'order_id': self._unserialise(int, job_details['order_id']),
                             'client_id': self._unserialise(int, job_details['client_id']),
                             'uuid': int(uuid),
                             'date': day,
                             'distance': self._unserialise_float(job_details['km']),
                             'cash': self._unserialise(bool, job_details['cash']),
                             'city_tour': self._unserialise_float(job_details['city_tour']),
                             'extra_stops': self._unserialise_float(job_details['extra_stops']),
                             'overnight': self._unserialise_float(job_details['overnight']),
                             'fax_confirm': self._unserialise_float(job_details['fax_confirm']),
                             'waiting_time': self._unserialise_float(job_details['waiting_time']),
                             'type': self._unserialise_type(job_details['type'])})

            clients.append(client)
            orders.append(order)

            for address in addresses:
                geocoded = self.geocode(address)

                checkpoint = Checkpoint(**{'checkpoint_id': geocoded['osm_id'],
                                           'display_name': geocoded['display_name'],
                                           'lat': geocoded['lat'],
                                           'lon': geocoded['lat'],
                                           'street': self._unserialise(str, address['address']),
                                           'city': self._unserialise(str, address['city']),
                                           'postal_code': self._unserialise(int, address['postal_code']),
                                           'company': self._unserialise(str, address['company'])})

                checkin = Checkin(**{'checkin_id': self._hash_timestamp(day, address['timestamp']),
                                     'checkpoint_id': geocoded['osm_id'],
                                     'order_id': self._unserialise(int, job_details['order_id']),
                                     'timestamp': self._unserialise_timestamp(day, address['timestamp']),
                                     'purpose': self._unserialise_purpose(address['purpose']),
                                     'after_': self._unserialise_timestamp(day, address['after']),
                                     'until': self._unserialise_timestamp(day, address['until'])})

                checkpoints.append(checkpoint)
                checkins.append(checkin)

            notify('Packaged {}-uuid-{}.', str(day), uuid)

        # The order matters when we commit to the database
        # because foreign keys must be refer to existing
        # rows in related tables, c.f. the model module.
        tables = (clients, orders, checkpoints, checkins)

        return tables

    @staticmethod
    def geocode(raw_address: dict) -> dict:
        """
        Geocode an address with Nominatim (http://nominatim.openstreetmap.org).
        The returned osm_id is used as the primary key in the checkpoint table.
        As a result, if we can't geocode an address, it will won't make it into
        the database.
        """
    
        g = Nominatim()

        json_address = {'postalcode': raw_address['postal_code'],
                        'street': raw_address['address'],
                        'city': raw_address['city'],
                        'country': 'Germany'}

        nothing = {'osm_id': None,
                   'lat': None,
                   'lon': None,
                   'display_name': None}

        if not all(json_address.values()):
            notify('Geocoding impossible: missing field(s).')
            return nothing
        else:
            try:
                response = g.geocode(json_address)
            except GeocoderTimedOut:
                notify('Nominatim timed out {}.', raw_address['address'])
                geocoded = nothing
            else:
                if response is None:
                    geocoded = nothing
                    verb = 'failed'
                else:
                    geocoded = response.raw
                    verb = 'matched'

                if DEBUG:
                    notify('Nominatim {} {}.', verb, raw_address['address'])

        return geocoded

    @staticmethod
    def _unserialise(type_cast: type, raw_value: str):
        """
        Dynamically type-cast raw strings returned by the scraper, with a twist:
        empty and None return None. The point is that the database will refuse to
        add a row if a non-nullable column gets the value None. That keeps the
        database nice and clean. The other variants of this function do the same.
        """
    
        if raw_value in (None, ''):
            return raw_value
        else:
            return type_cast(raw_value)

    @staticmethod
    def _unserialise_purpose(raw_value: str):
        """ This is a dirty fix """
        if raw_value is 'Abholung':
            return 'pickup'
        elif raw_value is 'Zustellung':
            return 'dropoff'
        else:
            return None

    @staticmethod
    def _unserialise_timestamp(day, raw_time: str):
        """ This is a dirty fix """
        if raw_time in ('', None):
            return None
        else:
            t = strptime(raw_time, '%H:%M')
            return datetime(day.year,
                            day.month,
                            day.day,
                            hour=t.tm_hour,
                            minute=t.tm_min)

    @staticmethod
    def _unserialise_type(raw_value: str):
        """ This is a dirty fix """
        if raw_value is 'OV':
            return 'overnight'
        elif raw_value is 'Ladehilfe':
            return 'help'
        elif raw_value is 'Stadtkurier':
            return 'city_tour'
        else:
            return None

    @staticmethod
    def _hash_timestamp(day, raw_time: str):
        """ This is a dirty fix """
        if raw_time in (None, ''):
            return None
        else:
            t = strptime(raw_time, '%H:%M')
            d = datetime(day.year,
                         day.month,
                         day.day,
                         hour=t.tm_hour,
                         minute=t.tm_min)
            return d.__hash__()

    @staticmethod
    def _unserialise_float(raw_price: str):
        """ This is a dirty fix """
        if raw_price in (None, ''):
            return None
        else:
            return float(raw_price.replace(',', '.'))


class Scraper:
    """ Basically, the Scraper class scrapes data fields from html files. """

    # Some tags are a target.
    _TAGS = dict(header={'name': 'h2', 'attrs': None},
                 client={'name': 'h4', 'attrs': None},
                 itinerary={'name': 'p', 'attrs': None},
                 prices={'name': 'tbody', 'attrs': None},
                 address={'name': 'div', 'attrs': {'data-collapsed': 'true'}})

    # Each field has a regex instructions.
    _BLUEPRINTS = {'itinerary': dict(km={'line_nb': 0, 'pattern': r'(\d{1,2},\d{3})\s', 'nullable': True}),
                   'header': dict(order_id={'line_nb': 0, 'pattern': r'.*(\d{10})', 'nullable': True},
                                  type={'line_nb': 0, 'pattern': r'.*(OV|Ladehilfe|Stadtkurier)', 'nullable': False},
                                  cash={'line_nb': 0, 'pattern': r'(BAR)', 'nullable': True}),
                   'client': dict(client_id={'line_nb': 0, 'pattern': r'.*(\d{5})$', 'nullable': False},
                                  client_name={'line_nb': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'nullable': False}),
                   'address': dict(company={'line_nb': 1, 'pattern': r'(.*)', 'nullable': False},
                                   address={'line_nb': 2, 'pattern': r'(.*)', 'nullable': False},
                                   city={'line_nb': 3, 'pattern': r'(?:\d{5})\s(.*)', 'nullable': False},
                                   postal_code={'line_nb': 3, 'pattern': r'(\d{5})(?:.*)', 'nullable': False},
                                   after={'line_nb': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'nullable': True},
                                   purpose={'line_nb': 0, 'pattern': r'(Abholung|Zustellung)', 'nullable': False},
                                   timestamp={'line_nb': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'nullable': False},
                                   until={'line_nb': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'nullable': True})}

    def __init__(self):
        pass

    @time_me
    @log_me
    def scrape(self, soup_items: list) -> list:
        """
        In goes a bunch of html files (in the form of beautiful soups),
        out comes serial data, i.e. dictionaries of field name/value
        pairs, where values are raw strings.

        :param soup_items: Stamped(Stamp, BeautifulSoup)
        :return: Stamped(Stamp, (job_details, addresses))
        """

        serial_items = list()

        for i, soup_item in enumerate(soup_items):
            job_details, addresses = self._scrape_job(soup_item)
            serial_item = Stamped(soup_item.stamp, (job_details, addresses))

            serial_items.append(serial_item)

            if DEBUG:
                notify('{}/{}. Scraped {}-uuid-{}.html',
                       i+1,
                       len(soup_items),
                       soup_item.stamp.date.strftime('%Y-%m-%d'),
                       soup_item.stamp.uuid)

                pp = PrettyPrinter()
                pp.pprint(serial_item)

        return serial_items

    def _scrape_job(self, soup_item: Stamped) -> tuple:
        """
        Scrape out of a job's web page using bs4 and re modules.
        In goes the soup, out come dictionaries contaning field
        sname/value pairs as raw trings.

        :param soup_item: the job's web page as a soup
        :return: job_details and addresses as a tuple
        """

        # Pass the soup through the sieve
        soup = soup_item.data.find(id='order_detail')

        # Step 1: scrape job details
        job_details = dict()

        # Step 1.1: everything except prices
        fragments = ['header', 'client', 'itinerary']

        for fragment in fragments:
            soup_fragment = soup.find_next(name=self._TAGS[fragment]['name'])
            fields_subset = self._scrape_fragment(self._BLUEPRINTS[fragment], soup_fragment,
                                                  soup_item.stamp.uuid, fragment)
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
            address = self._scrape_fragment(self._BLUEPRINTS['address'], soup_fragment,
                                            soup_item.stamp.uuid, 'address')

            addresses.append(address)

        return job_details, addresses

    def _scrape_fragment(self,
                         blueprint: dict,
                         soup_fragment: BeautifulSoup,
                         stamp: Stamp,
                         tag: str) -> dict:
        """
        Scrape a fragment of the page. In goes hmtl
        with the blueprint, out comes a dictionary.

        :param blueprint: the instructions
        :param soup_fragment: an html fragment
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
            try:
                matched = match(field['pattern'], contents[field['line_nb']])
            except IndexError:
                collected[field_name] = None
                if DEBUG:
                    self._elucidate(stamp, field_name, field, contents, tag)
            else:
                if matched:
                    collected[field_name] = matched.group(1)
                else:
                    collected[field_name] = None
                    if not field['nullable']:
                        if DEBUG:
                            self._elucidate(stamp, field_name, field, contents, tag)

        return collected

    @staticmethod
    def _scrape_prices(soup_fragment: BeautifulSoup) -> dict:
        """
        Scrape the 'prices' table at the bottom of the page. This section is
        scraped seperately because it's already neatly formatted as a table.

        :param soup_fragment: parsed html
        :return: item/price pairs
        """

        # TODO Get rid of the _scrape_prices() method!

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
            else:
                price_table[new] = None

        # The waiting time cell has the time in minutes
        # as well as the price. We just want the price.
        if price_table['waiting_time'] is not None:
            price_table['waiting_time'] = price_table['waiting_time'][7::]

        return price_table

    @staticmethod
    def _elucidate(stamp: Stamp, field_name: str, blueprint: dict, context: list, tag: str):
        """ Print a debug message showing the context in which the scraping went wrong.

        :param: stamp: holds the job date and uuid
        :param field_name: the name of the field
        :param blueprint: the field instructions
        :param context: the document fragment
        """

        seperator = '*' * 50
        print(seperator)

        print('{} {}: Failed to scrape {} from {} on line {}.'.format(stamp.date,
                                                                      stamp.uuid,
                                                                      field_name,
                                                                      context[blueprint['line']],
                                                                      blueprint['line'], tag))
        for line_nb, line in enumerate(context):
            print(str(line_nb) + ': ' + line + '\n')

        print(seperator)