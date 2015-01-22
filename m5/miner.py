import re
from bs4 import BeautifulSoup


class Miner:
    """
    The Miner class methods scrape off bike messenger data from the company server. They also package
    it up nicely so we can play with it later without inflicting upon ourselves any unnecessery pain.
    """

    # We use the BeautifulSoup4 module to extract information within specific html tags.
    # Yes... before we try and swallow a web page, we first cut it up into small pieces.
    _TAGS = dict(
        address={'name': 'div', 'attrs': {'data-collapsed': 'true'}},
        header={'name': 'h2', 'attrs': None},
        client={'name': 'h4', 'attrs': None},
        itinerary={'name': 'p', 'attrs': None},
        prices={'name': 'tbody', 'attrs': None}
    )

    # Each field has a blueprint. Where does it hide? What is it? Is it always there?
    # We bundle fields according to what sub-section they're in.
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
        self.debug_messages = []
        self.raw_data = None

    def fetch_jobs(self):
        """ Return unique 'uuid' request parameters for every job on that day.
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
        :return: (tag object) cleaned up html as produced by bs4
        """

        # Prepare the request and shoot
        url = self._server + 'll_detail.php5'
        payload = {'status': 'delivered', 'uuid': job}
        response = self._session.get(url, params=payload)

        # Turn it into a digestible soup
        # and filter out the tasty stuff
        soup = BeautifulSoup(response.text)
        return soup.find(id='order_detail')

    def _save_job(self, job_soup, job_uuid):
        """ From the soup, prettify the html and save it to file.

        :param job_soup: (tag object) the web page in soup form
        :param job_uuid: (str) the job's identifier
        """

        # TODO Current folder for now: user folders in the future
        f = self.date.strftime('%d.%m.%Y') + '-' + job_uuid + '.html'
        with open(f, 'w') as f:
            f.write(job_soup.prettify())
            f.close()

    def _scrape_subset(self, fields, soup_subset):
        """
        Scrape a sub-section of the html document. The document format very is unreliable:
        the number of lines in each section varies and the number of fields on each line
        also varies! For this reason, our scraping strategy is somewhat conservative.
        The motto is: one field at a time! The goal is to end up with a robust set of data.
        Failure to collect information is not a show-stopper but we should know about it!

        :param fields: (dict) the fields to be collected
        :param soup_subset: (tag object) the contents of a tag in soup form
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
                    # If we fail to scrape the field but the field is optional:
                    # assign a dictionary key anyways!
                    collected[name] = None
                else:
                    # If we fail to scrape a field that we actually need: ouch!
                    # Don't assign any key and make sure we give some feedback.
                    self._store_debug_message(name, item, contents)

        return collected

    def scrape_job(self, soup):
        """
        Scrape the shit out of a job's web page using BeautifulSoup and a little regex.
        In three steps: first jobs details, then the price table and finally the addresses.
        Job details and prices are returned as dictionaries, addresses as a list of dictionaries.
        Each dictionary contains scraped field name/value pairs. Values are returned as raw strings.

        :param soup: (tag object) the job's web page in soup form
        :return: (tuple) details, prices, addresses
        """

        # Where the all collected fields are stored
        details = dict()
        # Scrape chosen sections of the document
        subsets = ['header', 'client', 'itinerary']
        for subset in subsets:
            soup_subset = soup.find_next(name=self._TAGS[subset]['name'])
            fields_subset = self._scrape_subset(self._BLUEPRINTS[subset], soup_subset)
            # Put all sections in the same basket
            details.update(fields_subset)

        # Scrape the price table at the bottom of the page
        soup_subset = soup.find(self._TAGS['prices']['name'])
        prices = self._scrape_prices(soup_subset)

        # Scrape an arbitrary number of addresses
        soup_subsets = soup.find_all(name=self._TAGS['address']['name'], attrs=self._TAGS['address']['attrs'])
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
        ... and also cause it's kinda fun to do use 'zip', 'pop' and 'keys'.

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
        # TODO Data pre-processing comes here!
        self.raw_data = raw_data

    def _store_debug_message(self, name: str, item, contents):
        """
        Save a debug message showing the context in which the scraping went wrong.
        And while we're at it, save a copy of the html file for later inspection.

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
