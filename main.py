#!/usr/bin/python

"""

Project-x helps you become a better bike messenger!

This little program can be used by all freelancers working
for Messenger. Just provide your username and password and
the program will analyze the data that pertains to you
on the company server. Have fun!

IMPORTANT NOTE! THIS CODE CAN BE DANGEROUS:

As long as this program is used freely by the bike messenger
themselves, everything is cool. As soon as it's used by the
company management, however, all hell breaks loose. So managers
watch out: if you ever use my code to track the performance
of messengers, I will despise you and you will go to hell.

"""

# © Copyright 2014 Loic Jounot
#
# Project-x is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# Project-x is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# The GNU/GPL v3 is found here: http://www.gnu.org/licenses/.


from user import *


u = User()

# The general idea is to help the bike messenger log onto
# the company server. Once that's done, we let him do what
# he/she wants through a command prompt. The commands are
# kept really simple.

while not u.is_authenticated:
    u.authenticate()  # Test user credentials on the server

if u.is_returning():
    u.load_data()  # Don't mine data twice: fetch existing data

while u.is_active:
    u.prompt()  # Prompt the user until he quits

u.save_data()  # Save updated user data
u.save_log()  # Save the current log
u.disconnect()  # Terminate the server session
