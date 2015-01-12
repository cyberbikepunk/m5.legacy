import re
from bs4 import BeautifulSoup


class Miner:
    """
    The Miner class scrapes off data from the company server.
    """

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

    @property
    def has_been_mined(self):
        return False

    def fetch_jobs(self):
        """
        Return the jobs that the user has completed on a given day.
        Jobs are reached through a unique 'uuid' request parameter.

        :return: (set) A set of 'uuid' strings
        """
        path = 'll.php5'
        payload = {'status': 'delivered', 'datum': self.date.strftime('%d.%m.%Y')}
        response = self._session.get(self._server+path, params=payload)
        pattern = 'uuid=(\d{7})'
        jobs = re.findall(pattern, response.text)
        # The 'uuid' parameter appears twice (there are
        # two separate links) so dump the duplicates.
        return set(jobs)

    def scrape_job(self, html):
        """
        Regex as much as possible out of the html.

        :param job: (str) pretty html
        :return: (dict) data field/value pairs
        """
        return None

    def get_job(self, job):
        """
        Request the job's url and return pretty html.

        :param job: (str) the 'uuid' request parameter
        :return: (str) pretty html
        """
        url = self._server + 'll_detail.php5'
        payload = {'status': 'delivered', 'uuid': job}
        response = self._session.get(url, params=payload)
        soup = BeautifulSoup(response.text)
        html = soup.prettify()
        self._save_job(html=html, job=job)
        return html

    def _save_job(self, html, job):
        """
        Save the pretty html soup version of the job to file.
        """
        f = self.date.strftime('%d.%m.%Y') + '-' + job + '.html'
        f = open(f, 'w')
        f.write(html)
        f.close()

    def package_job(self, data):
        pass



