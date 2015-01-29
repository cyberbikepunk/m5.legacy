""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API. Once I'm happy, I'll write a web interface.
"""


from m5 import user
from datetime import datetime

u = user.Messenger('m-134', 'PASSWORD')

# Pick a date
date = datetime('19-12-2014')

# Play with the API
u.mine(date)
u.interpret(date)
