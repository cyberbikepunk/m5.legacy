""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API through a command prompt. Once I'm happy with it,
I'll put it up on my server and write a web interface.
"""


from m5 import user


u = user.Messenger('m-134', 'PASSWORD')
exit(0)
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
