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
    supply = get_current_supply()

    btc_response = requests.get('https://api.coinmarketcap.com/v1/ticker/bitcoin/?convert=USD').json()[0]
    btc_price = float(btc_response['price_usd'])
    # eth_response = requests.get('https://api.coinmarketcap.com/v1/ticker/ethereum/?convert=USD').json()[0]
    # eth_price = float(eth_response['price_usd'])

    ste_response = requests.get('https://stocks.exchange/api2/ticker').json()
    ste_data = {i['market_name']: i for i in ste_response if i['market_name'] == u'CLO_BTC'}

    item = ste_data.get(u'CLO_BTC', None)
    # eth_item = ste_data.get(u'CLO_ETH', None)

    if item and btc_price:
        price_usd = float(item['last']) * btc_price
        # eth_price_usd = float(eth_item['last']) * eth_price
        sat = float(item['last'])
        # eth = float(eth_item['last'])

        vol = float(item['vol'])
        # eth_vol = float(eth_item['vol'])

        min24h = float(item['bid'])
        max24h = float(item['ask'])

        # eth_min24h = float(eth_item['bid'])
        # eth_max24h = float(eth_item['ask'])

        await client.say(ctx.message.author.mention + ': Here is your info for CLO')
        embed = discord.Embed()
        embed.add_field(name = "Current Supply", value = "{}".format(localize(supply)))
        embed.add_field(name = "Market Cap", value = "$ {}".format(localize(price_usd * supply)))
        embed.add_field(name = "Volume CLO 24h", value = "{}".format(localize(vol, decimals = 4)))
        embed.add_field(name = "Current BTC", value = "{}".format(localize(sat, decimals = 8)))
        embed.add_field(name = "Min 24h BTC", value = "{}".format(localize(min24h, decimals = 8)))
        embed.add_field(name = "Max 24h BTC", value = "{}".format(localize(max24h, decimals = 8)))
        # embed.add_field(name = "Current ETH", value = "{}".format(localize(eth, decimals = 8)))
        # embed.add_field(name = "Min 24h ETH", value = "{}".format(localize(eth_min24h, decimals = 8)))
        # embed.add_field(name = "Max 24h ETH", value = "{}".format(localize(eth_max24h, decimals = 8)))
        embed.add_field(name = "Price USD/BTC", value = "$ {}".format(localize(price_usd, decimals = 4)))
        # embed.add_field(name = "Price USD/ETH", value = "$ {}".format(localize(eth_price_usd, decimals = 4)))
        #embed.add_field(name = "Price Average", value = "$ {}".format(
        #    localize((eth_price_usd + price_usd)/ 2, decimals = 4)))
        await client.say(embed = embed)
    else:
        await client.say(ctx.message.author.mention + ': Sorry api did not return results')


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
