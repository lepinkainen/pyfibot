"""Googlefight"""

def command_googlefight(user, channel, args):
    """Fight a google fight. Usage: googlefight <first combatant> <second combatant>"""

    from modules import googlefight
    
    nick = getNick(user)
    try:
        one, two = args.split()
    except ValueError:
        say(channel, "%s: Usage: googlefight <first combatant> <second combatant>" % nick)
        return
        
    onescore, twoscore, winner = googlefight.getFightResult(one, two)
    say(channel, "%s: GoogleFight: %s (%s) vs %s (%s), winner is %s" % (nick, one, onescore, two, twoscore, winner))
