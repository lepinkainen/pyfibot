# -*- coding: utf-8 -*-

#
#https://github.com/numberoverzero/bottom
#
#

import trollius
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('trollius')

class IRCClientProtocol(trollius.Protocol):
    transport = None

    def __init__(self, loop):
        self.loop = loop

    # connection is open, login
    def connection_made(self, transport):
        self.transport = transport

        print('Connected')
        info = ['NICK pyfibot_test\n',
                'USER pyfibot3 0 * :Trollius Test\n']
        transport.writelines(info)

    def data_received(self, data):
        lines = data.decode().split('\r\n')
        for line in lines:
            self._print_irc(line)

    def _print_irc(self, line):
        if not line: return
        if line.startswith(":"):
            try:
                info, data = line.split(':')[1:]
            except ValueError:
                print line
                return

            source, code, target = info.split(' ')[:3]
            d = {'source':source,
                 'code': code,
                 'target': target,
                 'data': data}
            print(d)
            if int(code) == 376:
                print("CONNECTED!")
                self.transport.write("JOIN :#pyfitest\n")
        else:
            print("CMD %s" % line)
            cmd, msg = line.split(":")
            if cmd == "PING":
                print("PONG")
                self.transport.write("PONG\n")

    def connection_lost(self, exc):
        print('The server closed the connection')
        print('Stop the event loop')
        self.loop.stop()

loop = trollius.get_event_loop()

ircprotocol = lambda: IRCClientProtocol(loop)

coro = loop.create_connection(ircprotocol,
                              'irc.nebula.fi', 6667)
loop.run_until_complete(coro)
loop.run_forever()
loop.close()
