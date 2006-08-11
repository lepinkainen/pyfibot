"""Google search"""

def command_google(user, channel, args):
    """Search google, returns the first result and its title. Usage: google <search terms>"""
    from util import google

    if not args: return
    
    data = google.doGoogleSearch(args)
    # remove bold tags added by google
    # TODO: Do this with BS
    if len(data.results) > 0:
        title = data.results[0].title.replace("<b>", "").replace("</b>", "")
        est_results = data.meta.estimatedTotalResultsCount
        say(channel, "%s (%s) (%s results)" % (data.results[0].URL, title, str(est_results)))
    else:
        say(channel, "No results for '%s'" % args)
