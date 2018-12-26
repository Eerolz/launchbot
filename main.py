#!/usr/bin/python3
import configparser
from discord.ext import commands
import launchlibrary
import asyncio
from datetime import datetime, timezone, timedelta
from formatters import *


configfile = "config.ini"
config = configparser.ConfigParser()
config.read(configfile)

authorities = config['AUTHORITIES']['Authorities'].split(',')
authorities = list(map(int, authorities))
powerroles = config['AUTHORITIES']['Powerroles'].split(',')
prefix = config['BOT']['Prefix'].strip("'")
TOKEN = config['BOT']['Token']




api = launchlibrary.Api()
bot = commands.Bot(command_prefix=prefix)


def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

async def send(ctx, msg, args):
    sent_msg = await ctx.send(msg)
    if '-k' not in args:
        await asyncio.sleep(15)
        await sent_msg.delete()


class Launchcommands:
    """Commands related to rocket launches."""

    @commands.command()
    async def nextlaunch(self, ctx, *args):
        """Tells information about next launch.

        -k        Does not automatically delete bot message.
        -n        Notifies launch notify group.
        -id       Includes launch ID.
        -d        Includes mission description.
        -v        Includes video URL.
        """
        launch = launchlibrary.Launch.next(api, 1)[0]
        launchname = launch.name
        launchtime_tz = launch.net
        utc = datetime.now(timezone.utc)
        tz = launchtime_tz.tzname()
        T = chop_microseconds(launchtime_tz - utc)
        launchtime = launchtime_tz.replace(tzinfo=None)
        probability = launch.probability
        if probability == -1:
            probabilitystr = "Probability not available."
        else:
            probabilitystr = str(probability) + "%"
        msg = ''
        if '-n' in args:
            msg = notify(msg, ctx)
        msg += '**__{0}__**\nNET {1} {2}\nWeather probability: {3}\nT- {4}\n'
        msg = msg.format(launchname, launchtime, tz, probabilitystr, T)
        for arg, formatter in (('-id', id), ('-d', description), ('-v', videourl)):
            if arg in args:
                msg = formatter(msg, launch)
        await send(ctx, msg, args)

    @commands.command()
    async def launchbyid(self, ctx, *args):
        """Tells information about launch with provided ID.

        [int]     ID of the launch.
        -k        Does not automatically delete bot message.
        -r        Includes holdreason and failreason
        -v        Includes video URL.
        -d        Includes mission description.
        """
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

    @commands.command()
    async def launchbyname(self, ctx, name, *args):
        """Tells information about launch with provided name.

        "str"     Name of the launch. (always first)
        -k        Does not automatically delete bot message.
        -id       Includes id of the launch.
        -r        Includes holdreason and failreason.
        -v        Includes video URL.
        -d        Includes mission description.
        """
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

    @commands.command()
    async def listbyname(self, ctx, name, *args):
        """Lists launches with provided name.

        [int]     The number of launches listed. Default is 5, max 10.
        -k        Does not automatically delete bot message.
        -id       Include the IDs of the launches.
        """
        num = 5
        for arg in args:
            if arg.isdigit():
                num = int(arg)
        launches = launchlibrary.Launch.fetch(api, name=name)
        msg = ""
        for launch in launches[:num]:
            msg += launch.name
            if "-s" in args:
                msg += ", Status: {0}".format(launch.get_status().name)
            if "-id" in args:
                msg += ", ID: {0}".format(launch.id)
            msg += "\n"
        await send(ctx, msg, args)

    @commands.command()
    async def listlaunches(self, ctx, *args):
        """Lists next launches.
        Note: only gives launches with determined launch windows.

        [int]     The number of launches listed. Default is 5, max is 10.
        -k        Does not automatically delete bot message.
        -s        Include launch status.
        -id       Include the IDs of the launches.
        """
        num = 5
        for arg in args:
            if arg.isdigit():
                num = int(arg)
        launches = launchlibrary.Launch.next(api, num)
        msg = ""
        for launch in launches:
            msg += launch.name
            if "-s" in args:
                msg += ", Status: {0}".format(launch.get_status().name)
            if "-id" in args:
                msg += ", ID: {0}".format(launch.id)
            msg += "\n"
        await send(ctx, msg, args)

    @commands.command()
    async def tminus(self, ctx):
        """Tells time to NET of next launch."""
        launch = launchlibrary.Launch.next(api, 1)[0]
        launchtime = launch.net
        utc = datetime.now(timezone.utc)
        T = chop_microseconds(launchtime - utc)
        sent_msg = await ctx.send('{0}'.format(T))
        await asyncio.sleep(5)
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
    """Allows moderators to kill the bot.
    Please don't abuse this, or I might have to remove it.
    """
    author = ctx.author
    roles = author.roles
    is_admin = False
    for role in roles:
        if str(role) in powerroles:
            is_admin = True
            break
    if author.id in authorities or is_admin:
        await ctx.send("If you say so ;(")
        await bot.logout()
    else:
        await ctx.send("You can't tell me what to do!")
bot.run(TOKEN)
