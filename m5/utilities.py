""" Miscellaneous utility classes and functions """

from datetime import datetime


class TimeMe():
    pass


def notify(message, *args):
    """
    Print a message to screen.
    """

    message = message.format(*args)
    timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
    tagged_message = timestamp + ' | ' + message
    print(tagged_message)



