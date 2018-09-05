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


def localize(value, decimals = 2):
    str_format = "{0:,.%df}" % decimals
    return str_format.format(value)


@client.event
async def on_ready():
    print ("Bot is Ready")
    print ("I am running on " + client.user.name)


@client.command(name='clo.cs', pass_context=True)
async def clo_current_supply(ctx):

    try:
        item = requests.get('https://api.coinmarketcap.com/v2/ticker/2757/?convert=BTC').json()['data']
    except KeyError:
        item = None

    if item:
        price_usd = float(item['quotes']['USD']['price'])
        price_btc = float(item['quotes']['BTC']['price'])
        supply = float(item['circulating_supply'])
        vol_btc = float(item['quotes']['BTC']['volume_24h'])
        rank = item['rank']

        embed = discord.Embed()
        embed.add_field(name = "Current Supply", value = "{}".format(localize(supply, decimals = 0)))
        embed.add_field(name = "Market Cap", value = "$ {}".format(localize(price_usd * supply)))
        embed.add_field(name = "Volume BTC 24h", value = "{}".format(localize(vol_btc, decimals = 4)))
        embed.add_field(name = "Rank", value = "{}".format(rank))
        embed.add_field(name = "Current BTC", value = "{}".format(localize(price_btc, decimals = 8)))
        embed.add_field(name = "Current USD", value = "$ {}".format(localize(price_usd, decimals = 4)))
        await client.say(embed = embed)
    else:
        await client.say(ctx.message.author.mention + ': Sorry api did not return results')


HASH_VALUES = [
    ('EH', 1000000000000000000),
    ('PH', 1000000000000000),
    ('TH', 1000000000000),
    ('GH', 1000000000),
    ('MH', 1000000),
    ('kH', 1000),
    ]

def resolve_hashrate(value):
    for symbol, amount in HASH_VALUES:
        if value >= amount:
            return (symbol, value / amount)
    return ('kH', float(0))


@client.event
async def on_command_error(error, *args, **kwargs):
    ctx = args[0]
    print(error)
    await client.send_message(
        ctx.message.channel,
        ctx.message.author.mention + ' Bad request. Please check ?clo.help')


@client.command(name='clo.help', pass_context=True)
async def help(ctx):
    help_message = """```Here are list of available commands:
    ?clo.help: Displays a list of available commands

    *** Supply ****

    ?clo.cs: Displays current supply, price from crypto compare and estimate marketcap
    ```"""
    await client.say(help_message)


client.run(os.environ['TOKEN'])
