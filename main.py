#!/usr/bin/python

__author__ = 'Loic Jounot (loic@cyberpunk.bike)'

import m5


# The general idea is to help the bike messenger log on
# the company server. Once that's done, we let him do what
# he wants through a command prompt. The commands are
# kept really simple.

# Log onto the company server
u = Messenger('m-134', 'PASSWORD')

if u.is_returning:              # Don't mine data twice: resurrect existing data
    u.load_data()

while u.is_active:              # Prompt the user until he quits
    date = u.prompt_date()      # TODO Extend the prompt to other commands
    u.mine(date)
    break                       # TODO Activate the loop once everything is cool
else:                           # Make a clean exit
    u.save_data()
    u.save_log()
    u.logout()
