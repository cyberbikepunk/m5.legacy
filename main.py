#!/usr/bin/python

__author__ = 'Loic Jounot (loic@cyberpunk.bike)'

import user


# The general idea is to help the bike messenger log on
# the company server. Once that's done, we let him do what
# he wants through a command prompt. The commands are
# kept really simple.

u = user.User()
u.authenticate()                # Log onto the company server

if u.is_returning:              # Don't mine data twice: fetch existing data
    u.load_data()

while u.is_active:              # Prompt the user until he quits
    date = u.prompt_date()
    u.mine(date)
    break                       # One day at a time for now
else:                           # Make a clean exit
    u.save_data()
    u.save_log()
    u.logout()
