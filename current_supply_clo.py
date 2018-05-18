# CLO Current supply bot by Pbzrpa

import os
import requests
import discord

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, relationship

from discord.ext.commands import Bot

BOT_PREFIX = "?"
CC_API_URL = 'https://min-api.cryptocompare.com/data/pricemulti'

MYSQL_USER = os.environ['CLO_MYSQL_USER']
MYSQL_PASS = os.environ['CLO_MYSQL_PASS']
MYSQL_DB = os.environ['CLO_MYSQL_DB']

try:
    SQLALCHEMY_ECHO = bool(os.environ['SQLALCHEMY_ECHO'])
except KeyError:
    SQLALCHEMY_ECHO = False


CONNECT_STRING = 'mysql+pymysql://{}:{}@localhost/{}?charset=utf8'.format(MYSQL_USER, MYSQL_PASS, MYSQL_DB)


Base = declarative_base()


class Offer(Base):
    __tablename__ = "offer"

    id = Column('id', Integer, primary_key = True)
    author_id = Column('author_id', String(64))
    amount = Column('amount', Float)
    price = Column('price', Float)
    author_nick = Column('author_nick', String(128), nullable = True)

    def __repr__(self):
        return "{}".format(self.id)


class Bid(Base):
    __tablename__ = "bid"

    id = Column('id', Integer, primary_key = True)
    author_id = Column('author_id', String(64))
    amount = Column('amount', Float)
    price = Column('price', Float)
    author_nick = Column('author_nick', String(128), nullable = True)

    def __repr__(self):
        return "{}".format(self.id)


class Banned(Base):
    __tablename__ = "banned"

    id = Column('id', Integer, primary_key = True)
    author_id = Column('author_id', String(64))


engine = create_engine(CONNECT_STRING, echo = SQLALCHEMY_ECHO)
Base.metadata.create_all(bind = engine)
Session = sessionmaker(bind=engine)


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
    ste_response = requests.get('https://stocks.exchange/api2/ticker').json()
    ste_data = {i['market_name']: i for i in ste_response}
    item = ste_data.get(u'CLO_BTC', None)
    if item and btc_price:
        price_usd = float(item['last']) * btc_price
        sat = float(item['last'])
        vol = float(item['vol'])
        min24h = float(item['bid'])
        max24h = float(item['ask'])

        await client.say(ctx.message.author.mention + ': Here is your info for CLO')
        embed = discord.Embed(title="CLO Stats", color=0x00ff00)
        embed.add_field(name = "Current Supply", value = "{}".format(localize(supply)))
        embed.add_field(name = "Market Cap", value = "$ {}".format(localize(price_usd * supply)))
        embed.add_field(name = "Volume CLO 24h", value = "{}".format(localize(vol, decimals = 4)))
        embed.add_field(name = "Current Sat", value = "{}".format(localize(sat, decimals = 8)))
        embed.add_field(name = "Min 24h Sat", value = "{}".format(localize(min24h, decimals = 8)))
        embed.add_field(name = "Max 24h Sat", value = "{}".format(localize(max24h, decimals = 8)))
        embed.add_field(name = "Price USD", value = "$ {}".format(localize(price_usd, decimals = 4)))
        await client.say(embed = embed)
    else:
        await client.say(ctx.message.author.mention + ': Sorry api did not return results')


# Offers


@client.command(name='clo.add_sell', pass_context=True)
async def add_sell(ctx, amount: float, price: float):

    session = Session()

    if session.query(Banned).filter_by(author_id = str(ctx.message.author.id)).first():
        await client.say(ctx.message.author.mention + ': Sorry you are not allowed to make offers')
        return

    offer = session.query(Offer).filter_by(author_id = str(ctx.message.author.id)).first()

    if offer:
        await client.say(ctx.message.author.mention + ': You already have an active offer #: {}'.format(offer.id))
        return
    else:
        if amount > 6500000000:
            await client.say(ctx.message.author.mention + ': Amount is greater that total supply')
        else:
            offer = Offer(author_id = ctx.message.author.id, author_nick = ctx.message.author.name,
                          amount = amount, price = price)
            session.add(offer)
            session.commit()
            await client.say(ctx.message.author.mention + ': New offer created: {}'.format(offer.id))
            await build_show_all(ctx)
            await get_possible_trades(ctx)
    session.close()


async def build_offers(ctx):
    data = {
        'author': [],
        'amount': [],
        'price': [],
        }

    server = ctx.message.author.server

    session = Session()
    offers = session.query(Offer).order_by(Offer.price.desc())
    if not offers:
        await client.say(ctx.message.author.mention + ': There is currently no active offers')
    else:
        for offer in offers:
            member = server.get_member(offer.author_id)
            if member:
                data['author'].append('@{}'.format(member.name))
                data['amount'].append(localize(offer.amount, decimals = 0))
                data['price'].append('$ {}'.format(localize(offer.price, decimals = 4)))
        if data['author']:
            embed = discord.Embed(title="CLO Selling", color=0xFF007A)
            embed.add_field(name = "User", value = "\n".join(data['author']))
            embed.add_field(name = "Selling CLO", value = "\n".join(data['amount']))
            embed.add_field(name = "Price Each", value = "\n".join(data['price']))
            await client.say(embed = embed)
        else:
            await client.say('No active offers found')
    session.close()


@client.command(name='clo.show_sell', pass_context=True)
async def show_sell(ctx):
    await build_offers(ctx)


@client.command(name='clo.del_sell', pass_context=True)
async def del_sell(ctx):
    session = Session()
    offer = session.query(Offer).filter_by(author_id = str(ctx.message.author.id)).first()

    if not offer:
        await client.say(
            ctx.message.author.mention + ': Did not find any of your offers')
        return
    else:
        session.delete(offer)
        session.commit()
        await client.say(ctx.message.author.mention + ': Your offer has been removed')
        await build_show_all(ctx)
    session.close()


# Bids


@client.command(name='clo.add_buy', pass_context=True)
async def add_buy(ctx, amount: float, price: float):

    session = Session()

    if session.query(Banned).filter_by(author_id = str(ctx.message.author.id)).first():
        await client.say(ctx.message.author.mention + ': Sorry you are not allowed to make bids')
        return

    bid = session.query(Bid).filter_by(author_id = str(ctx.message.author.id)).first()

    if bid:
        await client.say(ctx.message.author.mention + ': You already have an active bid #: {}'.format(bid.id))
        return
    else:
        if amount > 6500000000:
            await client.say(ctx.message.author.mention + ': Amount is greater that total supply')
        else:
            bid = Bid(author_id = ctx.message.author.id, author_nick = ctx.message.author.name,
                      amount = amount, price = price)
            session.add(bid)
            session.commit()
            await client.say(ctx.message.author.mention + ': New bid created: {}'.format(bid.id))
            await build_show_all(ctx)
            await get_possible_trades(ctx)
    session.close()


async def build_bids(ctx):
    data = {
        'author': [],
        'amount': [],
        'price': [],
        }

    server = ctx.message.author.server

    session = Session()
    bids = session.query(Bid).order_by(Bid.price.desc())
    if not bids:
        await client.say(ctx.message.author.mention + ': There is currently no active bids')
    else:
        for bid in bids:
            member = server.get_member(bid.author_id)
            if member:
                data['author'].append('@{}'.format(member.name))
                data['amount'].append(localize(bid.amount, decimals = 0))
                data['price'].append('$ {}'.format(localize(bid.price, decimals = 4)))
        if data['author']:
            embed = discord.Embed(title="CLO Buying", color=0x70a84d)
            embed.add_field(name = "User", value = "\n".join(data['author']))
            embed.add_field(name = "Buying CLO", value = "\n".join(data['amount']))
            embed.add_field(name = "Price Each", value = "\n".join(data['price']))
            await client.say(embed = embed)
        else:
            await client.say('No active bids found')
    session.close()


@client.command(name='clo.show_buy', pass_context=True)
async def show_buy(ctx):
    await build_bids(ctx)


async def build_show_all(ctx):
    await build_offers(ctx)
    await build_bids(ctx)


@client.command(name='clo.show_all', pass_context=True)
async def show_all(ctx):
    await build_show_all(ctx)


@client.command(name='clo.del_buy', pass_context=True)
async def del_buy(ctx):
    session = Session()
    bid = session.query(Bid).filter_by(author_id = str(ctx.message.author.id)).first()

    if not bid:
        await client.say(
            ctx.message.author.mention + ': Did not find any of your bids')
        return
    else:
        session.delete(bid)
        session.commit()
        await client.say(ctx.message.author.mention + ': Your bid has been removed')
        await build_show_all(ctx)
    session.close()


async def get_possible_trades(ctx):

    session = Session()

    bids = session.query(Bid).all()
    offers = session.query(Offer).all()

    session.close()

    mentions = set()

    if bids and offers:
        min_offer = min([i.price for i in offers])
        max_bid = max([i.price for i in bids])

        for offer in [i for i in offers if i.price <= max_bid]:
            mentions.add(discord.User(id = offer.author_id))

        for bid in [i for i in bids if i.price >= min_offer]:
            mentions.add(discord.User(id = bid.author_id))

    if mentions:
        mention_string = " ".join([i.mention for i in mentions])
        await client.say(mention_string + ' - Possible Trades Detected !!!')


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

    *** Sell Offers ***

    ?clo.add_sell [amount clo] [price each]: Add a new offer to sell. Only 1 offer per user.
    ?clo.del_sell: Remove your sell offer
    ?clo.show_sell: Display a list of current sell offers

    *** Bids ***

    ?clo.add_buy [amount clo] [price each]: Add a new bid to buy. Only 1 bid per user.
    ?clo.del_buy: Remove your buying bid
    ?clo.show_buy: Display a list of current buying bids

    *** All ***

    ?clo.show_all: Display both Offers and Bids

    ```"""
    await client.say(help_message)


client.run(os.environ['TOKEN'])
