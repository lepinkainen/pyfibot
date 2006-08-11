
import random

random.seed()

quotes = ["Greenhouse effect with the weed connect / DEA can't keep Greenthumb in check (Dr. Greenthumb)",
          "Like Louie Armstrong played the trumpet / I'll hit dat bong and break ya off something (Insane in the brain)",
          "Hit the joint, up the bomb, take a puff / Till you just can't get enough (Everybody must get stoned)",
          "To get to my point, I'm talkin about a ill trip / The Funky Cypress Hill Shit (Funky Cypress hill shit)",
          "My oven is on high, when I roast the quail / Tell Bill Clinton to go and inhale /Exhale, now you felt the funk of the power / now feel the effects... I want to get high (I wanna get high)",
          "Grab the weed up, pack it in, put it in the pipe / Light it up, smoke a bowl, we puffin the lye right / Put your finger on the hole and hold it in brother / Take a puff, that's enough, and pass it to another (High times)",
          "Pick it, pack it Fire it up Come along / And take a hit from the bong (Hits from the bong)",
          "Sing my song, puff all night long / As I take Hits from the bong... (Hits from the bong)",
          ]

def command_hash(user, channel, args):
    """Random Cypress Hill quote"""
    
    msg = random.choice(quotes)
    
    say(channel, msg)
