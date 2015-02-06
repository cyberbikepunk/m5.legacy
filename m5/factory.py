""" Miner and Processor classes. """

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
    """ The'process' method packages the raw data into tables digestable by the database. """

    def __init__(self, raw_data: tuple, date: datetime):

        self.clients = list()
        self.orders = list()
        self.checkpoints = list()
        self.checkins = list()

        self.raw_data = raw_data
        self.date = date

    def process(self):
        """ Process the raw data and produce ORM compatible table row objects. """

        for raw_datum in self.raw_data:
            job_details = raw_datum[0]
            addresses = raw_datum[1]

            client = Client(**{'client_id': self.unserialise(int, job_details['client_id']),
                               'name': self.unserialise(str, job_details['client_name'])})

            order = Order(**{'order_id': self.unserialise(int, job_details['order_id']),
                             'client_id': self.unserialise(int, job_details['client_id']),
                             'date': self.date,
                             'distance': self.unserialise(float, job_details['km']),
                             'cash': self.unserialise(bool, job_details['cash']),
                             'city_tour': self.unserialise(float, job_details['city_tour']),
                             'extra_stops': self.unserialise(float, job_details['extra_stops']),
                             'overnight': self.unserialise(float, job_details['overnight']),
                             'fax_confirm': self.unserialise(float, job_details['fax_confirm']),
                             'waiting_time': self.unserialise(float, job_details['waiting_time']),
                             'type': self.unserialise_type(job_details['type'])})

            self.clients.append(client)
            self.orders.append(order)

            for address in addresses:
                geocoded = self.geocode(address)

                checkpoint = Checkpoint(**{'checkpoint_id': geocoded['osm_id'],
                                           'display_name': geocoded['display_name'],
                                           'lat': geocoded['lat'],
                                           'lon': geocoded['lat'],
                                           'street': self.unserialise(str, job_details['address']),
                                           'city': self.unserialise(str, job_details['city']),
                                           'postal_code': self.unserialise(int, job_details['postal_code']),
                                           'company': self.unserialise(str, address['company'])})

                checkin = Checkin(**{'checkin_id': self.hash_timestamp(self.date, address['timestamp']),
                                     'checkpoint_id': geocoded['osm_id'],
                                     'order_id': self.unserialise(int, job_details['order_id']),
                                     'timestamp': self.unserialise_timestamp(self.date, address['timestamp']),
                                     'purpose': self.unserialise_purpose(address['purpose']),
                                     'after': self.unserialise_timestamp(self.date, address['after']),
                                     'until': self.unserialise_timestamp(self.date, address['until'])})

                self.checkpoints.append(checkpoint)
                self.checkins.append(checkin)

    @staticmethod
    def geocode(raw_address: dict) -> dict:
        """
        Geocode an address with Nominatim (http://nominatim.openstreetmap.org).
        The osm_id field is used as the primary key in the checkpoint table.
        """
    
        address = {'postalcode': raw_address['postal_code'],
                   'street': raw_address['address'],
                   'city': raw_address['city'],
                   'country': 'Germany'}
    
        geo = Nominatim()
        response = geo.geocode(address)
    
        geocoded = {'lat': response.raw['lat'],
                    'lon': response.raw['lon'],
                    'osm_id': response.raw['osm_id'],
                    'display_name': response.raw['display_name']}
    
        return geocoded

    @staticmethod
    def unserialise(type_cast: type, raw_value: str):
        """
        Dynamically cast-type raw strings returned by the scraper, with a twist:
        empty strings return None. The point is that the database will refuse to
        add a record if a non-nullable column gets the value None. That keeps the
        database nice and clean.
        """
    
        if raw_value is '':
            return None
        else:
            return type_cast(raw_value)

    @staticmethod
    def unserialise_purpose(raw_value):
        """ This is a dirty fix """
        if raw_value is 'Abholung':
            return 'pickup'
        elif raw_value is 'Zustellung':
            return 'dropoff'
        else:
            return None

    @staticmethod#
    def unserialise_timestamp(date, raw_time):
        """ This is a dirty fix """
        if raw_time is '':
            return None
        else:
            t = strptime(raw_time, '%H:%M')
            return datetime(date.year,
                            date.month,
                            date.day,
                            hour=t.tm_hour,
                            minute=t.tm_min)

    @staticmethod
    def unserialise_type(raw_value):
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
    def hash_timestamp(date, raw_time):
        """ This is a dirty fix """
        if raw_time is '':
            return None
        else:
            t = strptime(raw_time, '%H:%M')
            d = datetime(date.year,
                         date.month,
                         date.day,
                         hour=t.tm_hour,
                         minute=t.tm_min)
            return d.__hash__()


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
    _BLUEPRINTS = {'itinerary': dict(km={'line_nb': 0, 'pattern': r'(\d{1,2},\d{3})\sdistance', 'optional': True}),
                   'header': dict(order_id={'line_nb': 0, 'pattern': r'.*(\d{10})', 'optional': True},
                                  type={'line_nb': 0, 'pattern': r'.*(OV|Ladehilfe|Stadtkurier)', 'optional': False},
                                  cash={'line_nb': 0, 'pattern': r'(BAR)', 'optional': True}),
                   'client': dict(client_id={'line_nb': 0, 'pattern': r'.*(\d{5})$', 'optional': False},
                                  client_name={'line_nb': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'optional': False}),
                   'address': dict(company={'line_nb': 1, 'pattern': r'(.*)', 'optional': False},
                                   address={'line_nb': 2, 'pattern': r'(.*)', 'optional': False},
                                   city={'line_nb': 3, 'pattern': r'(?:\d{5})\s(.*)', 'optional': False},
                                   postal_code={'line_nb': 3, 'pattern': r'(\d{5})(?:.*)', 'optional': False},
                                   after={'line_nb': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'optional': True},
                                   purpose={'line_nb': 0, 'pattern': r'(Abholung|Zustellung)', 'optional': False},
                                   timestamp={'line_nb': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'optional': False},
                                   until={'line_nb': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'optional': True})}

    @staticmethod
    def build_blueprints():
        """ Construct regex blueprints from ORM field information """
        # TODO Write this function to dry the code
        pass

    def __init__(self, username: str, date: datetime, server: str, session: Session):
        """ Instantiate a Miner object for a given user and date.

        :param username: the current user
        :param date: a datetime object
        :param server: the url of the server
        :param session: the current
        """

        self.date = date
        self.server = server
        self.session = session
        self.username = username

    def filename(self, uuid):
        """ Construct a database filepath from a job uuid """
        return '../users/%s/%s_%s.html' % (self.username,
                                           self.date.strftime('%Y-%m-%d'),
                                           uuid)

    @time_me
    @log_me
    def mine(self) -> list:
        """
        Mine a given date from the server and return a list of
        tuples holding two dictionaries (job_details & addresses).
        """

        raw_data = list()

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

                raw_datum = self._scrape(soup, uuid)
                raw_data.append(raw_datum)

                notify('Mined {} OK.', self.date.strftime('%d-%m-%Y'))
                if self._DEBUG:
                    pp = PrettyPrinter()
                    pp.pprint(raw_datum)

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
        # ... save the file for future reference...
        self._save_job(soup, uuid)
        # ...and send back only what we need.
        job = soup.find(id='order_detail')

        return job

    def _scrape_fragment(self, blueprint: dict, soup_fragment: BeautifulSoup, uuid: str) -> dict:
        """ Scrape a fragment of the page. In goes hmtl + blueprint, out comes a dictionnary.

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
            # TODO Catch exceptions when line_nb doesn't exist
            matched = match(field['pattern'], contents[field['line_nb']])
            if matched:
                collected[field_name] = matched.group(1)
            else:
                collected[field_name] = ''
                if not field['optional']:
                    # We have a problem: make sure we log this so that we can fix it later
                    message = 'Failed to scrape {}: {}ll_detail.php5?status=delivered&uuid={}'
                    notify(message, field_name, self.server, uuid)

        return collected

    def _scrape(self, soup: BeautifulSoup, uuid) -> tuple:
        """
        Scrape out of a job's web page using bs4 and re modules.
        In comes the soup, out go field name/value pairs as raw
        strings.

        :param soup: the job's web page
        :return: job_details and addresses as a tuple
        """

        # Step 1: scrape job details
        job_details = dict()

        # Step 1.1: everything except prices
        fragments = ['header', 'client', 'itinerary']

        for fragment in fragments:
            soup_fragment = soup.find_next(name=self._TAGS[fragment]['name'])
            fields_subset = self._scrape_fragment(self._BLUEPRINTS[fragment],
                                                  soup_fragment,
                                                  uuid)
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
                                            uuid)

            addresses.append(address)

        raw_datum = (job_details, addresses)
        return raw_datum

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
        """ Prettify the html for that date and save it to file.

        :param job: the html soup for a given date
        """

        pretty_html = job.prettify()

        with open(self.filename(uuid), 'w+') as f:
            f.write(pretty_html)
            f.close()

        notify('File {} saved.', self.filename(uuid))