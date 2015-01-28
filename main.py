""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API through a command prompt. Once I'm happy,
I'll write a client-side web interface.
"""


from m5 import user


me = user.Messenger('m-134', 'PASSWORD')
while True:
    me.prompt()
