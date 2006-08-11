# -*- coding: iso-8859-1 -*-

"""Misc funny commands, nothing useful"""

import commands
import random

def command_remind(user, channel, args):
    """Remind someone of their skill level"""

    nick = getNick(user)
    args = args.strip()
    say(channel, "%s: http://reminder.ton.tut.fi (Courtesy of %s)" % (args, nick))

def command_takki(user, channel, args):
    """Get someone's coat."""

    if args:
        nick = args.strip()
    else:
        nick = getNick(user)
        
    me(channel, "hakee %sn takin narikasta." % nick)

def command_fortune(user, channel, args):
    """Prints a random quote"""
    
    cmd = "/usr/games/fortune -a -s"
    fortune = " ".join(commands.getoutput(cmd).split())
    say(channel, "%s" % fortune)

def command_fap(user, channel, args):
    """*fap* around a bit"""
    
    fapstr = "*"+"fap"*random.randint(2, 10)+"*"
    if(random.randint(1,10) > 5): fapstr = "%s *kruiks*" % fapstr
    say(channel, fapstr)

def command_kahvi(user, channel, args):
    """Get some coffee"""

    if args:
        target = args.split()[0]
    else:
        target = getNick(user)
        
    me(channel, "Hakee %slle kahvia" % target)

def command_vitsipirkka(user, channel, args):
    """Random joke"""

    bs = getUrl("http://www.plussa.com/?_tp=67,76", nocache=True).getBS()

    if not bs: return

    joke = bs.first('table', {'bgcolor':"#E8F1F9", 'border':"0", 'cellpadding':"0", 'cellspacing':"0", 'width':"419"}).fetch('td')[1].next.next.string

    # tidy up a lot
    joke = joke.strip().replace("\n", " ").replace("\r", "").replace("\x96", "-")
    
    say(channel, "Vitsipirkka: %s" % joke)

# kuka, mitä, missä, mitä tehtiin, mitä sitten tapahtui

def Xcommand_tunnustus(user, channel, args):
    """Random confession"""

    data = getUrl("http://tunnustuksien.luola.net/bulk.php", nocache=True).getContent()

    data.replace("\n", "")

    data = data.split(" ")

    id = data[0]
    date = data[1]
    tunnustus = " ".join(data[2:])
 
    say(channel, "Tunnustus %s:%s" % (id, tunnustus))
