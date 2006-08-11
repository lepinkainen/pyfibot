from twisted.application import service, internet

import pyfibot
import shelve

db = shelve.open("pyfibot.shelve")

application = service.Application("pyfibot")
s = service.IServiceCollection(application)

f = pyfibot.PyFiBotFactory(db)
f.createNetwork(("irc.kolumbus.fi", 6667), "ircnet", "pyfibot", ["#pyfitest"])
f.createNetwork(("efnet.xs4all.nl", 6667), "efnet", "pyfibot", ["#pyfitest"])
f.createNetwork(("irc.jyu.fi", 6667), "ircnet2", "pyfibot", ["#pyfitest"])

c1 = internet.TCPClient("irc.kolumbus.fi", 6667, f)
c1.setServiceParent(s)
#c2 = internet.TCPClient("irc.jyu.fi", 6667, f)
#c3 = internet.TCPClient("efnet.xs4all.net", 6667, f)

#c2.setServiceParent(s)
#c3.setServiceParent(s)
