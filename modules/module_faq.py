import os
import os.path
import sys
import re

# this should be faster than string.startswith
faqregex = re.compile(r'^\?\?') # matches strings starting with ??
faqignore = re.compile(r'(^[^\.])') # everything starting with a dot

def handle_privmsg(bot, user, channel, args):
    """Usage: ?? <searchterm>"""
    if faqregex.match(args):
        faqdir = os.path.join(sys.path[0], "faq", channel.replace("#", ""))
        if not os.path.exists(faqdir):
            bot.say(channel, "No FAQ for this channel")
            return

	# strip spaces from start & end, replace the rest with underscores
        args = args[2:].strip().replace(" ", "_")

	faqs = os.listdir(faqdir)
        faqs = filter(faqignore.match, faqs)
        if args in faqs:
            f = file(os.path.join(faqdir, args))
            value = f.read()
            f.close()

            # special case
            if channel == "#wow.crew":
                bot.say("#wow", value)
	else:
	    if len(faqs) > 0:
                bot.say(channel, "FAQs for this channel: " + ", ".join(faqs))
	    else:
		bot.say(channel, "No FAQ for this channel")

