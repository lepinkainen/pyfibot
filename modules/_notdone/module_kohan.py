

def command_kohan(user, channel, args):
    nick = getNick(user)

    players = ['Shrike', 'Fasti', 'McPolo', 'shang']

    if nick in players:
        say(channel, "%s: Kohania? (Request by %s)" % (", ".join(players), nick))
    else:
        notice(nick, "LOL XIITZOR HAXXOR!!!111")
