""" Miner and Processor classes. """
from geopy.exc import GeocoderTimedOut

from os.path import isfile
from geopy import Nominatim
from datetime import datetime
from time import strptime
from requests import Session
from bs4 import BeautifulSoup
from pprint import PrettyPrinter
from re import findall, match

from m5.utilities import notify, log_me, time_me
from m5.model import Checkin, Checkpoint, Client, Order

# TODO Refactor the miner module code DRY.
#   - blueprints (scraping specifications) should be defined
#     within the declarative model and unwrapped on the fly.
#   - the geo-coding and unserialisation procedures should
#     also be defined in the model and streamlined.
#   - we should get rid of corner cases: the price scraper
#     and all special un-serialisation methods


class Processor():
    """ The 'process' method packages scraped data into objects digestable by the database. """

    _DEBUG = True

    def __init__(self):
        pass

    def process(self, raw_data: tuple):
        """ Process scraped data and produce ORM compatible table row objects. """

        clients = list()
        orders = list()
        checkpoints = list()
        checkins = list()

        for raw_datum in raw_data:
            # Unpack each job
            date = raw_datum[0]
            uuid = raw_datum[1]
            job_details = raw_datum[2]
            addresses = raw_datum[3]

            client = Client(**{'client_id': self._unserialise(int, job_details['client_id']),
                               'name': self._unserialise(str, job_details['client_name'])})

            order = Order(**{'order_id': self._unserialise(int, job_details['order_id']),
                             'client_id': self._unserialise(int, job_details['client_id']),
                             'uuid': int(uuid),
                             'date': date,
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

                checkin = Checkin(**{'checkin_id': self._hash_timestamp(date, address['timestamp']),
                                     'checkpoint_id': geocoded['osm_id'],
                                     'order_id': self._unserialise(int, job_details['order_id']),
                                     'timestamp': self._unserialise_timestamp(date, address['timestamp']),
                                     'purpose': self._unserialise_purpose(address['purpose']),
                                     'after': self._unserialise_timestamp(date, address['after']),
                                     'until': self._unserialise_timestamp(date, address['until'])})

                checkpoints.append(checkpoint)
                checkins.append(checkin)

                notify('Processed {} {} successfully.', date, uuid)

        # Order matters for the database commits.
        tables = (clients, orders, checkpoints, checkins)
        return tables

    def geocode(self, raw_address: dict) -> dict:
        """
        Geocode an address with Nominatim (http://nominatim.openstreetmap.org).
        The returned osm_id is used as the primary key in the checkpoint table.
        """
    
        g = Nominatim()
        json_address = {'postalcode': raw_address['postal_code'],
                        'street': raw_address['address'],
                        'city': raw_address['city'],
                        'country': 'Germany'}

        if self._DEBUG:
            pp = PrettyPrinter()
            pp.pprint(json_address)

        _NOTHING = {'osm_id': None,
                    'lat': None,
                    'lon': None,
                    'display_name': None}
        try:
            geocoded = g.geocode(json_address)
        except GeocoderTimedOut:
            notify('Nominatim TIMED-OUT!. Skipping geocoding...')
            return _NOTHING

        if geocoded is not None:
            notify('Found {}.', geocoded.raw['display_name'])
            return geocoded.raw
        else:
            notify('FAILED to find <<<< {} >>>>.', json_address['street'])
            return _NOTHING

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
    def _unserialise_purpose(raw_value):
        """ This is a dirty fix """
        if raw_value is 'Abholung':
            return 'pickup'
        elif raw_value is 'Zustellung':
            return 'dropoff'
        else:
            return None

    @staticmethod
    def _unserialise_timestamp(date, raw_time):
        """ This is a dirty fix """
        if raw_time in ('', None):
            return None
        else:
            t = strptime(raw_time, '%H:%M')
            return datetime(date.year,
                            date.month,
                            date.day,
                            hour=t.tm_hour,
                            minute=t.tm_min)

    @staticmethod
    def _unserialise_type(raw_value):
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
    def _hash_timestamp(date, raw_time):
        """ This is a dirty fix """
        if raw_time in (None, ''):
            return None
        else:
            t = strptime(raw_time, '%H:%M')
            d = datetime(date.year,
                         date.month,
                         date.day,
                         hour=t.tm_hour,
                         minute=t.tm_min)
            return d.__hash__()

    @staticmethod
    def _unserialise_float(raw_price):
        """ This is a dirty fix """
        if raw_price in (None, ''):
            return None
        else:
            return float(raw_price.replace(',', '.'))


class Miner:
    """ Basically, the 'mine' method scrapes off data from the company server. """

    _DEBUG = True

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

    @staticmethod
    def build_blueprints():
        """ Construct regex blueprints from ORM field information """
        # TODO Write this function to dry the code
        pass

    def __init__(self, username: str, server: str, session: Session):
        """ Instantiate a Miner object for a given user and date.

        :param username: the current user
        :param server: the url of the server
        :param session: the current
        """

        self.server = server
        self.session = session
        self.username = username

        # Status flag
        self.date = None

    def filename(self, uuid):
        """ Construct the local filepath for a job. """
        return '../users/%s/%s_%s.html' % (self.username,
                                           self.date.strftime('%Y-%m-%d'),
                                           uuid)

    @time_me
    @log_me
    def mine(self, date: datetime) -> list:
        """
        Mine a given date from the server and return a list of
        tuples holding two dictionaries (job_details & addresses).
        """

        raw_data = list()
        self.date = date

        # Go browse the summary page for that day
        # and scrape off uuid parameters.
        uuids = self.scrape_uuids(date)

        # Was it a working day?
        if not uuids:
            notify('Nothing to mine on {}.', date.strftime('%d-%m-%Y'))
        else:
            i = 0
            total = len(uuids)
            for uuid in uuids:
                i += 1

                if self.is_cached(uuid):
                    soup = self.load_job(uuid)
                    verb = 'Loaded'
                else:
                    soup = self._get_job(uuid)
                    verb = 'Downloaded'

                if self._DEBUG:
                    notify('{}/{}. {} {} successfully.', i, total, verb, self.filename(uuid))

                job_details, addresses = self._scrape(soup, uuid)
                bundle = (date, uuid, job_details, addresses)
                raw_data.append(bundle)

                if self._DEBUG:
                    notify('{}/{}. Scraped {} successfully.', i, total, self.filename(uuid))
                    pp = PrettyPrinter()
                    pp.pprint(bundle)

        return raw_data

    def scrape_uuids(self, date: datetime) -> set:
        """
        Return unique uuid request parameters for each
        job by scraping the overview page for that date.
        These uuids are not strict uuids and not so unique:
        they are 7 digit numbers. But they're called uuids.

        :param date: a single day
        :return: A set of uuid strings
        """

        url = self.server + 'll.php5'
        payload = {'status': 'delivered',
                   'datum': date.strftime('%d.%m.%Y')}

        response = self.session.get(url, params=payload)

        pattern = 'uuid=(\d{7})'
        jobs = findall(pattern, response.text)

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
        # ... save the file for future reference.
        self._save_job(soup, uuid)

        return soup

    @staticmethod
    def _scrape_fragment(blueprint: dict,
                         soup_fragment: BeautifulSoup,
                         uuid: str,
                         tag: str) -> dict:
        """
        Scrape a fragment of the page. In goes hmtl + blueprint,
        out comes a dictionnary.

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
            matched = None

            try:
                matched = match(field['pattern'], contents[field['line_nb']])
            except IndexError:
                collected[field_name] = None
                notify('UUID={}. Failed to find {} on line {} inside {} fragment.',
                       uuid,
                       field_name.capitalize(),
                       field['line_nb'],
                       tag.capitalize())

            if matched:
                collected[field_name] = matched.group(1)
            else:
                collected[field_name] = None
                if not field['nullable']:
                    notify('UUID={}. Failed to match {} in {}.', uuid, field_name, field['pattern'])

        return collected

    def _scrape(self, soup: BeautifulSoup, uuid) -> tuple:
        """
        Scrape out of a job's web page using bs4 and re modules.
        In comes the soup, out go field name/value pairs as raw
        strings.

        :param soup: the job's web page
        :return: job_details and addresses as a tuple
        """

        soup = soup.find(id='order_detail')

        # Step 1: scrape job details
        job_details = dict()

        # Step 1.1: everything except prices
        fragments = ['header', 'client', 'itinerary']

        for fragment in fragments:
            soup_fragment = soup.find_next(name=self._TAGS[fragment]['name'])
            fields_subset = self._scrape_fragment(self._BLUEPRINTS[fragment],
                                                  soup_fragment,
                                                  uuid,
                                                  fragment)
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
            address = self._scrape_fragment(self._BLUEPRINTS['address'],
                                            soup_fragment,
                                            uuid,
                                            'address')

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
            else:
                price_table[new] = None

        # The waiting time cell has the time in minutes
        # as well as the price. We just want the price.
        if price_table['waiting_time'] is not None:
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

        with open(self.filename(uuid), 'r') as f:
            pretty_html = f.read()
            f.close()
        return BeautifulSoup(pretty_html)

    def _save_job(self, job: BeautifulSoup, uuid):
        """ Prettify the html for that date and save it to file.

        :param job: the html soup for a given date
        """

        pretty_html = job.prettify()

        with open(self.filename(uuid), 'w+') as f:
            f.write(pretty_html)
            f.close()
