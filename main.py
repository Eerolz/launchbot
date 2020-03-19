#!/usr/bin/python3
import configparser
import discord
from discord.ext import commands
import asyncio
from checks import *
import sqlite3
import configurations

configfile = "config.ini"
config = configparser.ConfigParser()
config.read(configfile)

prefix = config['BOT']['Prefix'].strip("'")
TOKEN = config['BOT']['Token']
testchannelid = int(config['BOT']['Testchannel'])

conn = sqlite3.connect('launcbot.db')
c = conn.cursor()

def get_prefix(client, message):
    c.execute("SELECT prefix FROM servers WHERE id=?", (message.guild.id,))
    server_prefix = c.fetchone()[0]
    if server_prefix:
        return [prefix, server_prefix]
    else:
        return prefix

bot = commands.Bot(command_prefix=get_prefix)
bot.add_cog(configurations.Configurations())

@bot.command(aliases=["die"])
@commands.check(is_owner)
async def shutdown(ctx):
    """Allows bots operators to shutdown the bot."""
    testchannel = bot.get_channel(testchannelid)
    author = ctx.author
    await testchannel.send(f'Killed by {author.name}, ({author.id})')
    await bot.logout()

@bot.command()
@commands.check(is_owner)
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency)}ms')

@bot.command()
@commands.check(is_owner)
async def test(ctx):
    msg = "test"
    await ctx.send(msg)

@bot.command(hidden=True)
@commands.check(can_answer)
async def jwst(ctx):
    await ctx.send("https://xkcd.com/2014/")

@bot.command(hidden=True)
@commands.check(is_owner)
async def say(ctx, channelid, message):
    channel = bot.get_channel(int(channelid))
    if channel:
        await channel.send(message)

@bot.event
async def on_ready():
    testchannel = bot.get_channel(testchannelid)
    await testchannel.send("Launchbot operational!")
    print("Launchbot operational!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        print(error)

bot.run(TOKEN)
conn.close()
