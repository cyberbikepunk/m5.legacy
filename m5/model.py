""" Model class and descendants. """


from datetime import datetime


class Model():
    """ Manage the database Model. """

    def __init__(self):
        pass

    DATABASE = {}

    # A tuple of 3 matching lists representing
    # fields, primary key & secondary keys
    TABLE = [dict()], [None], [list()]
    CHECKPOINTS = dict(
        job_id={'blueprint': None,
                'type': int, 'unit': None, 'optional': False, 'default': None,
                'primary': False, 'secondary': True},
        company={'blueprint': None,
                 'type': str, 'unit': None, 'optional': True, 'default': None,
                 'primary': False, 'secondary': False},
        address={'blueprint': None,
                 'type': str, 'unit': None, 'optional': False, 'default': None,
                 'primary': False, 'secondary': False},
        client_id={'blueprint': None,
                   'type': int, 'unit': None, 'optional': False, 'default': None,
                   'primary': False, 'secondary': True},
        client_name={'blueprint': None,
                     'type': str, 'unit': None, 'optional': True, 'default': None,
                     'primary': False, 'secondary': False},
        city={'blueprint': None,
              'type': str, 'unit': None, 'optional': True, 'default': 'Berlin',
              'primary': False, 'secondary': False},
        postal_code={'blueprint': None,
                     'type': int, 'unit': None, 'optional': False, 'default': None,
                     'primary': False, 'secondary': False},
        checkpoint_id={'blueprint': None,
                       'type': int, 'unit': None, 'optional': False, 'default': None,
                       'primary': True, 'secondary': False}
    )

    CHECKINS = dict(
        after={'blueprint': None,
               'type': datetime, 'unit': None, 'optional': True, 'default': None,
               'primary': False, 'secondary': False},
        until={'blueprint': None,
               'type': datetime, 'unit': None, 'optional': True, 'default': None,
               'primary': True, 'secondary': False},
        job_id={'blueprint': None,
                'type': int, 'unit': None, 'optional': False, 'default': None,
                'primary': False, 'secondary': True},
        timestamp={'blueprint': None,
                   'type': int, 'unit': None, 'optional': False, 'default': None,
                   'primary': True, 'secondary': False},
        checkin_id={'blueprint': None,
                    'type': int, 'unit': None, 'optional': False, 'default': None,
                    'primary': True, 'secondary': False},
        checkpoint_id={'blueprint': None,
                       'type': int, 'unit': None, 'optional': False, 'default': None,
                       'primary': False, 'secondary': True}
    )

    _BLUEPRINTS = dict(km={'line_number': 0, 'pattern': r'(\d{1,2},\d{3})\skm', 'optional': True},
                       job_id={'line_number': 0, 'pattern': r'.*(\d{10})', 'optional': True},
                       cash_payment={'line_number': 0, 'pattern': '(BAR)', 'optional': True},
                       client_id={'line_number': 0, 'pattern': r'.*(\d{5})$', 'optional': False},
                       client_name={'line_number': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'optional': False},
                       company={'line_number': 1, 'pattern': r'(.*)', 'optional': False},
                       address={'line_number': 2, 'pattern': r'(.*)', 'optional': False},
                       city={'line_number': 3, 'pattern': r'(?:\d{5})\s(.*)', 'optional': False},
                       postal_code={'line_number': 3, 'pattern': r'(\d{5})(?:.*)', 'optional': False},
                       after={'line_number': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'optional': True},
                       purpose={'line_number': 0, 'pattern': r'(Abholung|Zustellung)', 'optional': False},
                       timestamp={'line_number': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'optional': False},
                       until={'line_number': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'optional': True})

