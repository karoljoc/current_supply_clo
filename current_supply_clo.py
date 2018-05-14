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


CONNECT_STRING = 'mysql+pymysql://{}:{}@localhost/{}'.format(MYSQL_USER, MYSQL_PASS, MYSQL_DB)


Base = declarative_base()


class Offer(Base):
    __tablename__ = "offer"

    id = Column('id', Integer, primary_key = True)
    author_id = Column('author_id', String(64))
    amount = Column('amount', Float)
    price = Column('price', Float)

    def __repr__(self):
        return "{}".format(self.id)


engine = create_engine(CONNECT_STRING, echo = SQLALCHEMY_ECHO)
Base.metadata.create_all(bind = engine)
Session = sessionmaker(bind=engine)


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

def localize(value, decimals = 2):
    str_format = "{0:,.%df}" % decimals
    return str_format.format(value)


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


@client.command(name='clo.add_offer',
                pass_context=True)
async def add_offer(ctx, amount: float, price: float):

    session = Session()
    offer = session.query(Offer).filter_by(author_id = str(ctx.message.author.id)).first()

    if offer:
        await client.say(ctx.message.author.mention + ': You already have an active offer #: {}'.format(offer.id))
        return
    else:
        if amount > 6500000000:
            await client.say(ctx.message.author.mention + ': Amount is greater that total supply')
        else:
            offer = Offer(author_id = ctx.message.author.id, amount = amount, price = price)
            session.add(offer)
            session.commit()
            await client.say(ctx.message.author.mention + ': New offer created: {}'.format(offer.id))
    session.close()


@client.command(name='clo.show_offers',
                pass_context=True)
async def show_offers(ctx):
    data = {
        'author': [],
        'amount': [],
        'price': [],
        }

    server = ctx.message.author.server

    session = Session()
    offers = session.query(Offer).all()
    if not offers:
        await client.say(ctx.message.author.mention + ': There is currently no active offers')
    else:
        embed = discord.Embed(title="CLO Sell Offers", color=0x00ff00)
        for offer in offers:
            member = server.get_member(offer.author_id)
            if member:
                data['author'].append('@{}'.format(member.name))
                data['amount'].append(localize(offer.amount, decimals = 0))
                data['price'].append('$ {}'.format(localize(offer.price, decimals = 4)))
        if data['author']:
            embed = discord.Embed(title="CLO Sell Offers", color=0x00ff00)
            embed.add_field(name = "User", value = "\n".join(data['author']))
            embed.add_field(name = "Selling CLO", value = "\n".join(data['amount']))
            embed.add_field(name = "Price Each", value = "\n".join(data['price']))
            await client.say(embed = embed)
        else:
            await client.say('No active offers found')
    session.close()


@client.event
async def on_command_error(error, *args, **kwargs):
    ctx = args[0]
    await client.send_message(
        ctx.message.channel,
        ctx.message.author.mention + ' Bad request. Please check ?clo.help')


@client.command(name='clo.del_offer',
                pass_context=True)
async def del_offer(ctx):
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
    session.close()


@client.command(name='clo.help', pass_context=True)
async def help(ctx):
    help_message = """```Here are list of available commands:
    ?clo.help: Displays a list of available commands
    ?clocs: Displays current supply, price from crypto compare and estimate marketcap
    ?clo.add_offer [amount clo] [price each]: Add a new offer to sell. Only 1 offer per user.
    ?clo.show_offers: Display a list of current sell offers
    ?clo.del_offer: Remove your sell offer
    ```"""
    await client.say(help_message)


client.run(os.environ['TOKEN'])
