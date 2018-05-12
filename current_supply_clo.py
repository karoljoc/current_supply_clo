# CLO Current supply bot by Pbzrpa

import os
import requests
import discord

from discord.ext.commands import Bot

BOT_PREFIX = "?"
CC_API_URL = 'https://min-api.cryptocompare.com/data/pricemulti'

client = Bot(command_prefix=BOT_PREFIX)


def get_current_supply():
    response = requests.get('https://cloexplorer.org/total')
    return int(response.text)

def get_current_price():
    response = requests.get(CC_API_URL, params = {'fsyms': 'CLO', 'tsyms': 'USD'}).json()
    try:
        price = response['CLO']['USD']
    except KeyError:
        price = 0
    return price

def localize(value):
    return "{:,}".format(value)


@client.event
async def on_ready():
    print ("Bot is Ready")
    print ("I am running on " + client.user.name)


@client.command(name='clocs',
                pass_context=True)
async def clo_current_supply(ctx):
    supply = get_current_supply()
    price = get_current_price()

    await client.say(ctx.message.author.mention + ': Here is your info for CLO')
    embed = discord.Embed(title="CLO Current Supply Info", color=0x00ff00)
    embed.add_field(name = "Current Supply", value = "{} CLO".format(localize(supply)))
    embed.add_field(name = "Price Crypto Compare", value = "$ {}".format(localize(price)))
    embed.add_field(name = "Estimated Market Cap", value = "$ {}".format(localize(price * supply)))
    await client.say(embed = embed)


    old ="""
    messages = [
        'Current Supply: {}'.format(localize(supply)),
        'Current Price Crypto Compare: ${}'.format(localize(price)),
        'Estimated Market Cap: ${}'.format(localize(price * supply))
        ]
    await client.say(context.message.author.mention + ': Here is your info for CLO')
    await client.say('```{}```'.format('\n'.join(messages)))
    """

client.run(os.environ['TOKEN'])
