#!/usr/bin/python

import user


u = user.User()

# The general idea is to help the bike messenger log onto
# the company server. Once that's done, we let him do what
# he/she wants through a command prompt. The commands are
# kept really simple.

while not u.is_authenticated:
    u.authenticate()  # Test user credentials on the server

if u.is_returning():
    u.load_data()  # Don't mine data twice: fetch existing data

while u.is_active:
    u.prompt_date()  # Prompt the user until he quits
else:
    u.clean_exit()
