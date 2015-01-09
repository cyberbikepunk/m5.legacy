import re


class Miner:
    """
    The Miner class scrapes data off the company server.
    """

    def __init__(self, date, session, server):
        """
        Initialize all class attributes.

        :param date: (datetime obj) date to be mined
        :param session: (request.session obj) current session
        :param server: (str) server url
        """
        self.date = date
        self._session = session
        self._server = server
        self.regex = ''

    def has_been_mined(self):
        return False

    def fetch_jobs(self):
        """
        Return all the jobs that the user has completed on a given day.
        Each job has unique 'uuid' request parameter.

        :return: (set) A set of 'uuid' strings
        """
        path = 'll.php5'
        payload = {'status': 'delivered', 'datum': self.date.strftime('%d.%m.%Y')}
        response = self._session.get(self._server+path, params=payload)
        pattern = 'uuid=(\d{7})'
        jobs = re.findall(pattern, response.text)
        # The 'uuid' parameter appears twice for each
        # job (i.e. there are two separate links) so
        # let'S get rid of the duplicates.
        return set(jobs)

    def scrape_job(self, job):
        """
        Request the job's url and scrape as much information
        as we can using the regex engine.

        :param job: (str) the 'uuid' request parameter for that job
        :return: (dict) field/value pairs
        """
        url = self._server + 'll_detail.php5'
        payload = {'status': 'delivered', 'uuid': job}
        response = self._session.get(url, params=payload)
        return self._compiled_regex.match(response.text)

    @property
    def _compiled_regex(self):
        """
        Define the regex groups for the fields we're trying to scrape
        and compile the regex pattern.

        :return: (re.pattern obj)
        """
        fields = {'id': r'<h2>(?P<{}>\d{10})',
                  'type': r'\|\s(?P<{}>\w*),',
                  'stops': r'(?P<{}>Stadtstop)'}

        groups = []
        for name, pattern in fields.items():
            groups.append(pattern.format(name))

        regex = re.compile(' '.join(groups))
        return regex

    def package_job(self, data):
        pass



