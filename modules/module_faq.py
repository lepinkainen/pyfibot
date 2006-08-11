import os
import os.path
import sys

def handle_privmsg(bot, user, channel, args):
    """Usage: ?? <searchterm>"""
    if args.startswith("??"):
        faqdir = os.path.join(sys.path[0], "faq", channel.replace("#", ""))
        if not os.path.exists(faqdir):
            bot.say(channel, "No FAQ for this channel")
            return

	# strip spaces from start & end, replace the rest with underscores
        args = args[2:].strip().replace(" ", "_")

	faqs = os.listdir(faqdir)
        if args in faqs:
            f = file(os.path.join(faqdir, args))
            value = f.read()
            f.close()
            if channel == "#wow.crew":
                value = "!msg #wow "+value
            bot.say(channel, value)
	else:
	    if len(faqs) > 0:
                bot.say(channel, "FAQs for this channel: " + ", ".join(faqs))
	    else:
		bot.say(channel, "No FAQ for this channel")

