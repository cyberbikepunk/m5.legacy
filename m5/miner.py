""" Miner classes and related stuff. """

import re

from datetime import datetime
from requests import Session
from bs4 import BeautifulSoup
from pprint import PrettyPrinter

from m5.utilities import notify


class Miner:
    """
    The 'mine' method scrapes off data from the company server.
    It's the only public method in the class. Everything else
    is low-level internals.
    """

    _DEBUG = True

    # Specify the relevant tags in the DOM tree.
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
            company={'line_number': 1, 'pattern': r'(.*)', 'optional': False},
            address={'line_number': 2, 'pattern': r'(.*)', 'optional': False},
            city={'line_number': 3, 'pattern': r'(?:\d{5})\s(.*)', 'optional': False},
            postal_code={'line_number': 3, 'pattern': r'(\d{5})(?:.*)', 'optional': False},
            after={'line_number': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'optional': True},
            purpose={'line_number': 0, 'pattern': r'(Abholung|Zustellung)', 'optional': False},
            timestamp={'line_number': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'optional': False},
            until={'line_number': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'optional': True}
        ),
        header=dict(
            job_id={'line_number': 0, 'pattern': r'.*(\d{10})', 'optional': True},
            cash_payment={'line_number': 0, 'pattern': '(BAR)', 'optional': True}
        ),
        client=dict(
            client_id={'line_number': 0, 'pattern': r'.*(\d{5})$', 'optional': False},
            client_name={'line_number': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'optional': False}
        ),
        itinerary=dict(
            km={'line_number': 0, 'pattern': r'(\d{1,2},\d{3})\skm', 'optional': True}
        )
    )

    def __init__(self, dates: set, server: str, session: Session):
        """
        Initialize class attributes.

        :param dates: a set of datetime objects
        :param server: the url of the server
        :param session: the current
        """

        self.dates = dates
        self._server = server
        self._session = session

        # Used only in debug mode
        self._warnings = list()

    @time_me
    @log_me
    def mine(self) -> list:
        """
        Mine a set of dates from the server.

        :return: a list of (jobs, addresses) tuples
        """

        jobs = list()
        pp = PrettyPrinter()

        for date in dates:
            # Go browse the summary page for that day
            # and scrape off 'uuid' parameters.
            job_ids = self._fetch_job_ids(date)

            # Was it a working day?
            if job_ids:

                for job_id in job_ids:
                    soup = self._get_job(job_id)
                    job = self._scrape_job(soup)

                    if self._DEBUG:
                        pp.pprint(job)

                    jobs.append(jobs)

                notify('Mined {} OK.', date.strftime('%d-%m-%Y'))

        return jobs

    def _fetch_job_ids(self, date: datetime) -> set:
        """
        Return unique 'uuid' request parameters for each job
        by scraping the overview page for that date.

        :param date: a single day
        :return: A set of 'uuid' strings
        """

        url = self._server + 'll.php5'
        payload = {'status': 'delivered',
                   'datum': date.strftime('%d.%m.%Y')}
        response = self._session.get(url, params=payload)

        if self._DEBUG:
            self._save_html(response.text, date=date)

        pattern = 'uuid=(\d{7})'
        jobs = re.findall(pattern, response.text)

        # Each uuid string appears twice: dump the duplicates.
        return set(jobs)

    def _get_job(self, uuid: str) -> BeautifulSoup:
        """
        Get the page for that date and return a beautiful soup.

        :param uuid: the 'uuid' request parameter
        :return: parsed html soup
        """

        url = self._server + 'll_detail.php5'
        payload = {'status': 'delivered', 'uuid': uuid}

        response = self._session.get(url, params=payload)

        if self._DEBUG:
            self._save_html(response.text, uuid)

        # Parse the raw html text
        soup = BeautifulSoup(response.text)
        # Return only what we need
        order_detail = soup.find(id='order_detail')

        return order_detail

    @staticmethod
    def _save_html(raw_html: str, date: datetime=None, stamp: str=None) -> str:
        """
        Prettify the html and save it for debugging.

        :param raw_html: from the response object
        :param date:
        :param stamp: (str) the job's identifier
        """



    def _scrape_subset(self, blueprint: dict, soup_subset: BeautifulSoup) -> dict:
        """
        Scrape a sub-section of the html document using the blueprints.

        :param blueprint: the instructions
        :param soup_subset: the html fragment
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
            match = re.match(field['pattern'], contents[field['line_number']])
            if match:
                collected[name] = match.group(1)
            else:
                if field['optional']:
                    # If we fail to scrape the field but the field is optional:
                    # assign the dictionary key anyways:
                    collected[name] = None
                else:
                    # If we fail to scrape a field that we actually need: ouch!
                    # Don't assign any key and make sure we give some feedback.
                    self._log_warning(name, field, contents)
                    self._save_html()

        return collected

    def _scrape_job(self, soup: BeautifulSoup) -> tuple:
        """
        Scrape out of a job's web page using BeautifulSoup and a little regex.
        Job details are returned as a dictionary and addresses as a list of
        dictionaries. Field values are returned as raw strings.

        :param soup: the job's web page
        :return: job_details and addresses as a tuple
        """

        # Step 1: scrape job details
        job_details = dict()

        # Step 1.1: everything except prices
        subsets = ['header', 'client', 'itinerary']

        for subset in subsets:
            soup_subset = soup.find_next(name=self._TAGS[subset]['name'])
            fields_subset = self._scrape_subset(self._BLUEPRINTS[subset], soup_subset)
            job_details.update(fields_subset)

        # Step 1.2: the price table
        soup_subset = soup.find(self._TAGS['prices']['name'])
        prices = self._scrape_prices(soup_subset)
        job_details.update(prices)

        # Step 2: scrape an arbitrary number of addresses
        soup_subsets = soup.find_all(name=self._TAGS['address']['name'],
                                     attrs=self._TAGS['address']['attrs'])

        addresses = list()
        for soup_subset in soup_subsets:
            address = self._scrape_subset(self._BLUEPRINTS['address'], soup_subset)
            addresses.append(address)

        job = job_details, addresses
        return job

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

        # Original field names are no good. Change theself.
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

    def _add_warning(self, name: str, field: dict, context: list):
        """
        Store a debug message explaining where the scraping went wrong.

        :param name: (str) the name of the field
        :param field: (dict) the field blueprint
        :param context: (list) the context as a list of lines
        """

        date_string = date.strftime('%d-%m-%Y')

        soup = BeautifulSoup(raw_html)
        pretty_html = soup.prettify()

        path = '../debug/' + date_string + '-' + stamp + '.html'

        with open(path, 'w') as f:
            f.write(pretty_html)
            f.close()
        self.debug_messages.append('*' * 50)

        # The warning message
        template = 'Could not scrape "{}" from "{}" on line {}\n'
        warning = template.format(name, context[field['line_number']], field['line_number'])
        self.warnings.append(warning)

        # Give the full context.
        for field, content in enumerate(context):
            self.debug_messages.append(str(field) + ': ' + content)
