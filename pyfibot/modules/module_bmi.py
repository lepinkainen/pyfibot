"""
"""
from __future__ import unicode_literals, print_function, division


def calc_bmi(height, weight):
    return (float(weight) / height ** 2) * 10000


def print_bmi(bmi):
    if bmi < 16.5:
        weight_category = "severely underweight (less than 16.5)"
    elif bmi < 18.5:
        weight_category = "underweight (from 16.5 to 18.4)"
    elif bmi < 25:
        weight_category = "normal (from 18.5 to 24.9)"
    elif bmi < 30.1:
        weight_category = "overweight (from 25 to 30)"
    elif bmi < 35:
        weight_category = "obese class I (from 30.1 to 34.9)"
    elif bmi <= 40:
        weight_category = "obese class II (from 35 to 40)"
    else:
        weight_category = "obese class III (over 40)"

    return "your bmi is %.2f which is %s" % (bmi, weight_category)


def command_bmi(bot, user, channel, args):
    """Calculates your body mass index. Usage: bmi height(cm)/weight(kg)"""
    data = args.split("/")
    if len(data) != 2:
        return bot.say(channel, "Usage: bmi height(cm)/weight(kg)")
    else:
        return bot.say(channel, print_bmi(calc_bmi(int(data[0]), int(data[1]))))
