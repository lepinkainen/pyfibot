import namedays
import time

def command_date(user, channel, args):
    gmtime = time.gmtime()
    datestr = time.strftime("%A %d.%m.%Y %H:%M")
    datestr += " | Namedays: "+namedays.get_nameday(gmtime.tm_mon, gmtime.tm_mday)

    say(channel, datestr)
