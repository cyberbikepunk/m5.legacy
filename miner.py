import re
from bs4 import BeautifulSoup


class Miner:
    """
    The Miner class scrapes off data from the company server, cleans it up and packages it
    nicely so we can pickle it and play with it.
    """

    # We use BeautifulSoup4 to zoom in on contents within specific
    # html tags. This makes the regex engine modular and reliable.
    _TAGS = dict(
        address={'name': 'div', 'attrs': {'data-collapsed': 'true'}},
        header={'name': 'h2', 'attrs': None},
        client={'name': 'h4', 'attrs': None},
        itinerary={'name': 'p', 'attrs': None},
        prices={'name': 'tbody', 'attrs': None}
    )

    # The blueprint for each target field for the regex engine
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
        """
        Initialize class attributes.

        :param date: (datetime obj) date to be mined
        :param session: (request.session obj) current session
        :param server: (str) server url
        """
        self.date = date
        self._session = session
        self._server = server
        self.debug_messages = []

    def fetch_jobs(self):
        """
        Return a unique 'uuid' request parameters for each job the user has completed on a given day.

        :return: (set) A set of 'uuid' strings
        """
        url = self._server + 'll.php5'
        payload = {'status': 'delivered', 'datum': self.date.strftime('%d.%m.%Y')}
        response = self._session.get(url, params=payload)
        pattern = 'uuid=(\d{7})'
        jobs = re.findall(pattern, response.text)
        # The 'uuid' parameter appears twice (there are
        # two separate links): so dump the duplicates.
        return set(jobs)

    def get_job(self, job):
        """
        Request the job's url and return a beautiful html soup.

        :param job: (str) the 'uuid' request parameter
        :return: (str) pretty html
        """
        url = self._server + 'll_detail.php5'
        payload = {'status': 'delivered', 'uuid': job}
        response = self._session.get(url, params=payload)
        soup = BeautifulSoup(response.text)
        self._save_job(soup=soup, job=job)
        return soup.find(id='order_detail')

    def _save_job(self, soup, job):
        """
        Prettify the html soup and save it to file.

        :param soup: (tag object) cleaned up html as returned by Beautifulsoup
        :param job: (str) the job uuid
        """
        f = self.date.strftime('%d.%m.%Y') + '-' + job + '.html'
        with open(f, 'w') as f:
            f.write(soup.prettify())
            f.close()

    def _scrape_subset(self, fields, soup_subset):
        """
        Scrape a sub-section of the html document. The document format very is unreliable:
        the number of lines in each section varies and the number of fields on each line
        also varies! For this reason, our scraping strategy is... well... conservative.
        The motto is: one field at a time! The goal is to end up with a robust set of data.
        Failure to collect information is not a show-stopper but we should know about it!

        :param fields: (dict) the fields to be collected
        :param soup_subset: (tag object) cleaned up html
        :return: (dict) field name/value pairs
        """
        contents = list(soup_subset.stripped_strings)

        collected = dict()
        for name, item in fields.items():
            match = re.match(item['pattern'], contents[item['line']])
            if match:
                collected[name] = match.group(1)
            else:
                if item['optional']:
                    collected[name] = None
                else:
                    self._store_debug_message(name, item, contents)

        return collected

    def scrape_job(self, soup):
        """
        Scrape the shit out of the html document using BeautifulSoup and a little regex.
        Job details are returned as a dictionary and addresses as a list of dictionaries.
        Each dictionary contains field name/value pairs. All values are raw strings.

        :param soup: (tag object) cleaned up html produced by BeautifulSoup
        :return: (tuple) details, addresses
        """
        details = dict()

        # Scrape various sections in the document
        subsets = ['header', 'client', 'itinerary']
        for subset in subsets:
            soup_subset = soup.find_next(name=self._TAGS[subset]['name'])
            fields_subset = self._scrape_subset(self._BLUEPRINTS[subset], soup_subset)
            details.update(fields_subset)

        # Scrape prices at the bottom of the page
        soup_subset = soup.find(self._TAGS['prices']['name'])
        prices = self._scrape_prices(soup_subset)

        # Scrape an arbitrary number of addresses
        soup_subsets = soup.find_all(name=self._TAGS['address']['name'], attrs=self._TAGS['address']['attrs'])
        addresses = list()
        for soup_subset in soup_subsets:
            address = self._scrape_subset(self._BLUEPRINTS['address'], soup_subset)
            addresses.append(address)

        # Package it up nicely
        raw_data = details, prices, addresses
        return raw_data

    def _scrape_prices(self, soup_subset):
        """
        Scrape off the 'prices' table at the bottom of the page. This section is scraped seperately
        because it's already neatly formatted as a table.

        :param soup_subset: (tag object) cleaned up html
        :return: (dict) field name/value pairs
        """
        # The table is grabbed as a one-dimensional list
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
        # Keep my eyes open for more OV flavours

        for old, new in keys:
            if old in price_table:
                price_table[new] = price_table.pop(old)

        # The waiting time has a time field in minutes
        # as well as the price. We just want the price.
        if 'waiting_time' in price_table.keys():
            price_table['waiting_time'] = price_table['waiting_time'][7::]

        return price_table

    def package_job(self, data):
        pass

    def _store_debug_message(self, name: str, item, contents):
        """
        Save a debug message showing exactly where the scraping went wrong.

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
