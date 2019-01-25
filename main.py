#!/usr/bin/python3
import os
import sys
import subprocess
import configparser
import discord
from discord.ext import commands
import launchlibrary
import asyncio
from datetime import datetime, timezone, timedelta
from formatters import *
from random import choice


configfile = "config.ini"
config = configparser.ConfigParser()
config.read(configfile)

# bot operators
authorities = config['AUTHORITIES']['Authorities']
if authorities:
    authorities = authorities.split(',')
    authorities = list(map(int, authorities))
else:
    authorities = []
# bot configuration
prefix = config['BOT']['Prefix'].strip("'")
TOKEN = config['BOT']['Token']
# other bot settings
can_notify = config['SETTINGS'].getboolean('Can_notify')
keep_message = config['SETTINGS'].getboolean('Keep_message')
# channel limitation settings
limit_channels = config['CHANNELS'].getboolean('Is_limited')
if limit_channels:
    channels = config['CHANNELS']['Channels'].split(',')


api = launchlibrary.Api()
bot = commands.Bot(command_prefix=prefix)


def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

async def send(ctx, msg, args):
    sent_msg = await ctx.send(msg)
    if '-k' not in args and not keep_message:
        await asyncio.sleep(15)
        await sent_msg.delete()

def can_answer(ctx):
    if limit_channels:
        author = ctx.author
        if (ctx.channel.name in channels
        or author.server_permissions.administrator
        or author.id in authorities):
            return True
        else:
            return False
    else:
        return True

def get_next_update(launch):
    """How often will launchalertupdater check for updates."""
    launchtime_tz = launch.net
    utc = datetime.now(timezone.utc)
    T = chop_microseconds(launchtime_tz - utc)
    T_minus = T
    T_plus = timedelta(0)
    if T < timedelta(0):
        T_plus = chop_microseconds(utc - launchtime_tz)
        T = T_plus
    if launch.get_status().id in (2, 3, 4, 7):
        return -1
    elif T < timedelta(minutes=10):
        return 10
    elif T < timedelta(hours=1):
        return round(T.total_seconds()/60)
    elif T < timedelta(hours=2):
        return 60
    elif T_plus < timedelta(hours=6) or T_minus > timedelta(0):
        return 15*60
    else:
        return -1

async def alertupdater(launch, channel):
    launchid = launch.id
    next_update = 0
    while next_update != -1:
        new_data = False
        launch_last = launch
        launchlist = launchlibrary.Launch.fetch(api, id=launchid)
        if launchlist:
            launch = launchlist[0]
            msg = 'New data for **{0}**:\n'.format(launch.name)
            status = launch.get_status()
            if launch_last.get_status() != status:
                new_data = True
                msg += 'Status: {0}\n'.format(status.description)
                if status.id in (2, 4, 5, 7):
                    if launch.holdreason:
                        reason = launch.holdreason
                    else:
                        reason = launch.failreason
                    msg += 'Reason: {0}\n'.format(reason)
            if launch_last.probability != launch.probability:
                probability = launch.probability
                if probability != -1:
                    new_data = True
                    msg += 'Weather probability: {0}%\n'.format(probability)
            if new_data:
                await channel.send(content=msg)
        next_update = get_next_update(launch)
        await asyncio.sleep(next_update)

async def launchalertformatter(ctx, launch):
    """Formats the message for launchalert"""
    launchtime_tz = launch.net
    utc = datetime.now(timezone.utc)
    T_minus = chop_microseconds(launchtime_tz - utc)
    T_plus = timedelta(0)
    T = T_minus
    if T_minus < timedelta(0):
        T_plus = chop_microseconds(utc - launchtime_tz)
        T = T_plus
        T_str = "T+ {0}".format(T_plus)
    else:
        T_str = "T- {0}".format(T_minus)
    launchname = launch.name
    tz = launchtime_tz.tzname()
    launchtime = launchtime_tz.replace(tzinfo=None)
    probability = launch.probability
    launchstatus = launch.get_status()
    if probability == -1:
        probabilitystr = " not available"
    else:
        probabilitystr = '{0}%'.format(probability)
    msg = ''
    if can_notify:
        msg = notify(msg, ctx)
    else:
        msg = "Notifying disabled.\n"
    msg += '**__{0}__**\nNET {1} {2}\nWeather probability: {3}\n{4}\nStatus: {5}\n'
    msg = msg.format(launchname, launchtime, tz, probabilitystr, T_str, launchstatus.description)
    for formatter in (description, videourl):
        msg = formatter(msg, launch)
    return msg

class Launchcommands:
    """Commands related to rocket launches."""

    @commands.command(aliases=['nl', 'nela'])
    async def nextlaunch(self, ctx, *args):
        """Tells information about next launch.

        -k        Does not automatically delete bot message.
        -n        Notifies launch notify group.
        -id       Includes launch ID.
        -d        Includes mission description.
        -v        Includes video URL.
        """
        if not can_answer(ctx):
            return
        launch = launchlibrary.Launch.next(api, 1)[0]
        launchname = launch.name
        launchtime_tz = launch.net
        utc = datetime.now(timezone.utc)
        tz = launchtime_tz.tzname()
        T = chop_microseconds(launchtime_tz - utc)
        launchtime = launchtime_tz.replace(tzinfo=None)
        probability = launch.probability
        if probability == -1:
            probabilitystr = "not available"
        else:
            probabilitystr = '{0}%'.format(probability)
        msg = ''
        if '-n' in args:
            if can_notify:
                msg = notify(msg, ctx)
            else:
                msg = "Notifying disabled. "
        msg += '**__{0}__**\nNET {1} {2}\nWeather probability: {3}\nT- {4}\n'
        msg = msg.format(launchname, launchtime, tz, probabilitystr, T)
        for arg, formatter in (('-id', id), ('-d', description), ('-v', videourl)):
            if arg in args:
                msg = formatter(msg, launch)
        await send(ctx, msg, args)


    @commands.command()
    async def launchalert(self, ctx, alerttime='15'):
        """Enables launch alerts until next shutdown.
        Only authorities can use this.

        [int]     Minutes before launch to alert. (default = 15)
        """
        if not can_answer(ctx):
            return
        author = ctx.author
        if author.guild_permissions.administrator or author.id in authorities:
            if len(alerttime) < 6:
                alerttime = int(alerttime)
                msg = "Launch alerts enabled. Alerts at T- {0}minutes".format(alerttime)
                await ctx.send(msg)
                channel = ctx.message.channel
                launchid = None
                while 1:
                    launch = launchlibrary.Launch.next(api, 1)
                    if launch:
                        launch = launch[0]
                        launchtime_tz = launch.net
                        utc = datetime.now(timezone.utc)
                        T = chop_microseconds(launchtime_tz - utc)
                        if T < timedelta(minutes=alerttime) and launch.id != launchid:
                            msg = await launchalertformatter(ctx, launch)
                            await channel.send(msg)
                            updaterloop = asyncio.create_task(alertupdater(launch, channel))
                            await updaterloop
                            launchid = launch.id
                        else:
                            await asyncio.sleep(40)
            else:
                await ctx.send("You sure would like to know early.")
        else:
            await ctx.send("You don't have permission to do that.")

    @commands.command(aliases=['laid'])
    async def launchbyid(self, ctx, *args):
        """Tells information about launch with provided ID.

        [int]     ID of the launch.
        -k        Does not automatically delete bot message.
        -r        Includes holdreason and failreason
        -v        Includes video URL.
        -d        Includes mission description.
        """
        if not can_answer(ctx):
            return
        launchid = False
        for arg in args:
            if str(arg).isdigit():
                launchid = int(arg)
        if launchid:
            launch = launchlibrary.Launch.fetch(api, id=launchid)[0]
            launchname = launch.name
            launchstatus = launch.get_status().description
            launchtime_tz = launch.net
            tz = launchtime_tz.tzname()
            launchtime = launchtime_tz.replace(tzinfo=None)
            msg = '**__{0}__**\n{1}\nNET {2} {3}\n'
            msg = msg.format(launchname, launchstatus, launchtime, tz)
            for arg, formatter in (('-r', reasons), ('-d', description), ('-v', videourl)):
                if arg in args:
                    msg = formatter(msg, launch)
        else:
            msg = "No ID provided."
        await send(ctx, msg, args)

    @commands.command(aliases=['lana'])
    async def launchbyname(self, ctx, name, *args):
        """Tells information about launch with provided name.

        "str"     Name of the launch. (always first)
        -k        Does not automatically delete bot message.
        -id       Includes id of the launch.
        -r        Includes holdreason and failreason.
        -v        Includes video URL.
        -d        Includes mission description.
        """
        if not can_answer(ctx):
            return
        launches = launchlibrary.Launch.fetch(api, name=name)
        if launches:
            launch = launches[0]
            launchname = launch.name
            launchstatus = launch.get_status().description
            launchtime_tz = launch.net
            tz = launchtime_tz.tzname()
            launchtime = launchtime_tz.replace(tzinfo=None)
            msg = '**__{0}__**\n{1}\nNET {2} {3}\n'
            msg = msg.format(launchname, launchstatus, launchtime, tz)
            for arg, formatter in (('-r', reasons), ('-id', id), ('-d', description), ('-v', videourl)):
                if arg in args:
                    msg = formatter(msg, launch)
        else:
            msg = "No launch found with name provided."
        await send(ctx, msg, args)

    @commands.command(aliases=['lina'])
    async def listbyname(self, ctx, name, *args):
        """Lists launches with provided name.

        [int]     The number of launches listed. Default is 5, max 10.
        -k        Does not automatically delete bot message.
        -s        Include launch status.
        -id       Include the IDs of the launches.
        """
        if not can_answer(ctx):
            return
        num = 5
        for arg in args:
            if arg.isdigit():
                num = int(arg)
        launches = launchlibrary.Launch.fetch(api, name=name)
        msg = "**Listing launches found with {0}:**\n".format(name)
        if launches:
            for launch in launches[:num]:
                msg += launch.name
                if "-s" in args:
                    msg += ", Status: {0}".format(launch.get_status().name)
                if "-id" in args:
                    msg += ", ID: {0}".format(launch.id)
                msg += "\n"
        else:
            msg = "No launches found with provided name."
        await send(ctx, msg, args)

    @commands.command(aliases=['lila'])
    async def listlaunches(self, ctx, *args):
        """Lists next launches.
        Note: only gives launches that are GO.

        [int]     The number of launches listed. Default is 5, max is 10.
        -k        Does not automatically delete bot message.
        -s        Include launch status.
        -id       Include the IDs of the launches.
        """
        if not can_answer(ctx):
            return
        num = 5
        for arg in args:
            if arg.isdigit():
                num = int(arg)
        launches = launchlibrary.Launch.next(api, num)
        msg = "**Listing next launches:**\n"
        for launch in launches:
            msg += launch.name
            if "-s" in args:
                msg += ", Status: {0}".format(launch.get_status().name)
            if "-id" in args:
                msg += ", ID: {0}".format(launch.id)
            msg += "\n"
        await send(ctx, msg, args)

    @commands.command(aliases=['tm'])
    async def tminus(self, ctx):
        """Tells time to NET of next launch."""
        if not can_answer(ctx):
            return
        launch = launchlibrary.Launch.next(api, 1)[0]
        launchtime = launch.net
        utc = datetime.now(timezone.utc)
        T = chop_microseconds(launchtime - utc)
        sent_msg = await ctx.send('{0}'.format(T))
        if not keep_message:
            await asyncio.sleep(15)
            await sent_msg.delete()

bot.add_cog(Launchcommands())

class Rocketcommands:
    """Commands related to rockets."""

    @commands.command()
    async def rocketbyname(self, ctx, name, *args):
        """Tells information about rocket with provided name.

        "str"     Name of the rocket. (always first)
        -k        Does not automatically delete bot message.
        -id       Includes id of the rocket.
        -fid      Includes rocketfamily id.
        -aid      Includes agency id.
        -p        Includes pad ids.
        -w        Includes wikipedia URL.
        """
        if not can_answer(ctx):
            return
        rockets = launchlibrary.Rocket.fetch(api, name=name)
        if rockets:
            rocket = rockets[0]
            rocketname = rocket.name
            msg = '**__{0}__**\n'
            msg = msg.format(rocketname)
            for arg, formatter in (('-id', id), ('-fid', familyid), ('-aid', agencyid), ('-p', padids), ('-w', rocketwikiurl)):
                if arg in args:
                    msg = formatter(msg, rocket)
        else:
            msg = "No rocket found with name provided."
        await send(ctx, msg, args)

    @commands.command()
    async def rocketbyid(self, ctx, *args):
        """Tells information about rocket with provided ID.

        [int]     ID of the rocket.
        -k        Does not automatically delete bot message.
        -fid      Includes rocketfamily id.
        -aid      Includes agency id.
        -p        Includes pad ids.
        -w        Includes wikipedia URL.
        """
        if not can_answer(ctx):
            return
        for arg in args:
            if arg.isdigit():
                id = int(arg)
        rockets = launchlibrary.Rocket.fetch(api, id=id)
        if rockets:
            rocket = rockets[0]
            rocketname = rocket.name
            msg = '**__{0}__**\n'
            msg = msg.format(rocketname)
            for arg, formatter in (('-fid', familyid), ('-aid', agencyid), ('-p', padids), ('-w', rocketwikiurl)):
                if arg in args:
                    msg = formatter(msg, rocket)
        else:
            msg = "No ID provided."
        await send(ctx, msg, args)

bot.add_cog(Rocketcommands())

@bot.command(name="die")
async def shutdown(ctx):
    """Allows bots operator to kill the bot."""
    author = ctx.author
    if author.id in authorities:
        msgs = ('My life is forfeit!', 'If you say so :´(', 'Your wish is my command!',
        'Anything for you milord!', ":´(", 'NOOOOOOOOOOOOOOOOOoooooooo.......',
        'My life for Aiur!')
        msg = choice(msgs)
        await ctx.send(msg)
        f = "killers.txt"
        killlog = open(f, 'a')
        killlog.write(str(author.id))
        await bot.logout()
    else:
        await ctx.send("You can't tell me what to do!")

@bot.command()
async def pull(ctx):
    """Allows bots operator to update the bot."""
    author = ctx.author
    if author.id in authorities:
        out = subprocess.Popen(['git', 'pull'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate()
        stdout = stdout.decode("utf-8")
        msg = '**Output: **{0}\n'.format(stdout)
        if stderr:
            stderr = stderr.decode("utf-8")
            msg += '**Error: **\n{0}'.format(stderr)
        await ctx.send(msg)
    else:
        await ctx.send("You can't tell me what to do!")


@bot.command(name="restart")
async def restart_cmd(ctx):
    """Allows bots operator to restart the bot."""
    author = ctx.author
    if author.id in authorities:
        msg = "Restarting myself..."
        await ctx.send(msg)
        f = "killers.txt"
        killlog = open(f, 'a')
        killlog.write(str(author.id)+' restart')
        restarter = asyncio.create_task(restart())
        print(msg)
        await restarter
        await bot.logout()
    else:
        await ctx.send("You can't tell me what to do!")

async def restart():
    await asyncio.sleep(10)
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.command()
async def git(ctx):
    """Gives link to the bot's github page."""
    if can_answer(ctx):
        msg = "https://github.com/Eerolz/launchbot"
        await ctx.send(msg)

@bot.event
async def on_ready():
    act_def = discord.Activity(type=discord.ActivityType.watching, name='Launch Library')
    print("Launchbot operational!")
    while 1:
        launchlist = launchlibrary.Launch.next(api, 1)
        if launchlist:
            launch = launchlist[0]
        launchtime = launch.net
        utc = datetime.now(timezone.utc)
        T = chop_microseconds(launchtime - utc)
        name = 'countdown: {0}'.format(T)
        act_T = discord.Activity(type=discord.ActivityType.watching, name=name)
        await bot.change_presence(activity=act_T)
        if T < timedelta(minutes=5):
            check = 5
        elif T < timedelta(hours=1):
            check = round(T.total_seconds()/60)
        elif T < timedelta(hours=2):
            check = 60
        elif T < timedelta(days=1):
            check = 15*60
        else:
            check = 60*60
            await bot.change_presence(activity=act_def)
        await asyncio.sleep(check)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        print(error)

bot.run(TOKEN)
