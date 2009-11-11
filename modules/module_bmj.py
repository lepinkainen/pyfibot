def calc_bmj(height, weight):
    return  (float(weight)/height**2)*10000

def print_bmj(bmj):
    if bmj < 16.5:
        weight_category = "severely underweight (less than 16.5)"
    elif bmj < 18.5:
        weight_category = "underweight (from 16.5 to 18.4)"
    elif bmj < 25:
        weight_category = "normal (from 18.5 to 24.9)"
    elif bmj < 30.1:
        weight_category = "overweight (from 25 to 30)"
    elif bmj < 35:
        weight_category = "obese class I (from 30.1 to 34.9)"
    elif bmj <= 40:
        weight_category = "obese class II (from 35 to 40)"
    else:
        weight_category = "obese class III (over 40)"

    return("your BMJ is %.2f which is %s" % (bmj, weight_category))

def command_bmj(bot, user, channel, args):
    """Calculates your body mass index. Usage: .bmj height(cm)/weight(kg)"""
    data = args.split("/")
    if len(data) == 2:
        bot.say(channel, print_bmj(calc_bmj(int(data[0]), int(data[1]))))
    else:
        bot.say(channel, "error with arguments")
