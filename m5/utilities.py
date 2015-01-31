""" Miscellaneous utility classes and fs """

from datetime import datetime


def log_me(f):
    return f


def time_me(f):
    return f


def safe_io(f):
    return f


def safe_request(f):
    return f


def notify(message, *args):
    """ Print a message to the screen. """

    message = message.format(*args)
    timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
    notification = timestamp + ' | ' + message
    print(notification)


def area():
    """ Postal code area polygon
    :return:
    """
    pass
