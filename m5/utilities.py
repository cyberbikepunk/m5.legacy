""" Miscellaneous functions """

from datetime import datetime


def record(message, *args):
    """ Print a useful message to screen. """

    message = message.format(*args)
    timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
    tagged_message = timestamp + ' | ' + message
    print(tagged_message)