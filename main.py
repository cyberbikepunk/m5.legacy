""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API through a command prompt. Once I'm happy with it,
I'll put it on my server and write a client-side web interface for it.
"""


from m5 import user


u = user.Messenger('m-134', 'PASSWORD')
while True:
    u.prompt()
