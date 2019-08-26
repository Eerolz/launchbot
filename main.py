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
# channel settings
alertchannels = config['CHANNELS']['Alertchannels']
if alertchannels:
    alertchannels = alertchannels.split(',')
    alertchannels = list(map(int, alertchannels))
else:
    alertchannels = []
testchannelid = config['CHANNELS']['Testchannel']
if testchannelid:
    testchannelid = int(testchannelid)
else:
    testchannelid = None


api = launchlibrary.Api()
bot = commands.Bot(command_prefix=prefix)

alert_active = False #because I didn't come up with better way to deal with this problem

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

async def send(ctx, msg, args):
    sent_msg = await ctx.send(msg)


def can_answer(ctx):
    return True

agencycolors = {124:16750899, 27:16750899, 121:16777215, 147:0, 63:26112, 194:11155486}

def get_color(agencyid):
    if agencyid in agencycolors:
        return agencycolors[agencyid]
    else:
        print('No color for: {0}'.format(agencyid))
        return 5592405

async def launchalertformatter(launch):
    """Formats the message for launchalert (doesn't include mention)"""
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
    if probability == -1:
        probabilitystr = " not available"
    else:
        probabilitystr = '{0}%'.format(probability)
    embedcolor = discord.Colour(get_color(launch.agency.id))
    embed = discord.Embed(title=launchname, colour=embedcolor)
    embed.set_footer(text="ID: {0}".format(launch.id))
    embed.add_field(name="T-: {0}".format(T), value=launch.missions[0]['description'])
    embed.set_thumbnail(url=launch.rocket.image_url)
    embed.add_field(name="NET", value=timelink(launch.net), inline=True)
    embed.add_field(name="Maximum holding time:", value=launch.windowend - launch.net, inline=True)
    embed.add_field(name="Weather probability", value=probabilitystr)
    streamurls = launch.vid_urls
    if streamurls:
        url = streamurls[0]
    else:
        url = "No video available"

    return embed, url

class Launchcommands(commands.Cog):
    """Commands related to rocket launches."""

    @commands.command(aliases=['nl', 'nela'])
    async def nextlaunch(self, ctx, *args):
        """Tells information about next launch.

        -t       Includes launch window.
        -w        Includes weather probability.
        -v        Includes stream URLs.
        """
        if not can_answer(ctx):
            return
        launches = launchlibrary.Launch.next(api, 1)
        if launches:
            launch = launches[0]
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
            embedcolor = discord.Colour(get_color(launch.agency.id))
            embed = discord.Embed(title=launchname, colour=embedcolor)
            embed.set_footer(text="ID: {0}".format(launch.id))
            embed.add_field(name="T-: {0}".format(T), value=launch.missions[0]['description'])
            embed.set_thumbnail(url=launch.rocket.image_url)
            if '-t' in args:
                embed.add_field(name="Window start", value=timelink(launch.windowstart), inline=True)
                embed.add_field(name="NET", value=timelink(launch.net), inline=True)
                embed.add_field(name="Window end", value=timelink(launch.windowend), inline=True)
            else:
                embed.add_field(name="NET", value=timelink(launch.net), inline=True)
                embed.add_field(name="Max hold time:", value=launch.windowend - launch.net, inline=True)
            if '-w' in args:
                embed.add_field(name="Weather probability", value=probabilitystr)
            if '-v' in args:
                streamurls = launch.vid_urls
                if streamurls:
                    url = '\n'.join(streamurls)
                else:
                    url = "No video available"
                embed.add_field(name="Video", value=url)
            await ctx.send(embed=embed)


    @commands.command(hidden=True)
    async def launchalert(self, ctx, alerttime='15'):
        """Enables launch alerts until next shutdown.
        Only authorities can use this.

        [int]     Minutes before launch to alert. (default = 15, max = 99)
        """
        author = ctx.author
        if author.guild_permissions.administrator or author.id in authorities:
            await ctx.send("Command currently disabled")
            # if len(alerttime) < 2:
            #     alerttime = int(alerttime)
            #     msg = "Launch alerts enabled. Alerts at T- {0}minutes".format(alerttime)
            #     await ctx.send(msg)
            # else:
            #     await ctx.send("You sure would like to know early.")

    @commands.command(aliases=['laid'])
    async def launchbyid(self, ctx, *args):
        """Tells information about launch with provided ID.

        [int]     ID of the launch.
        -r        Includes holdreason and failreason
        -v        Includes video URLs.
        """
        if not can_answer(ctx):
            return
        launchid = False
        for arg in args:
            if str(arg).isdigit():
                launchid = int(arg)
        if launchid:
            launches = launchlibrary.Launch.fetch(api, id=launchid)
            if launches:
                launch = launches[0]
                launchname = launch.name
                launchstatus = launch.get_status().description
                launchtime_tz = launch.net
                tz = launchtime_tz.tzname()
                launchtime = launchtime_tz.replace(tzinfo=None)
                embedcolor = discord.Colour(get_color(launch.agency.id))
                embed = discord.Embed(title=launchname, colour=embedcolor)
                embed.set_footer(text="ID: {0}".format(launch.id))
                embed.set_thumbnail(url=launch.rocket.image_url)
                embed.add_field(name=launch.net, value=launch.missions[0]['description'])
                if '-r' in args:
                    holdreason = launch.holdreason
                    failreason = launch.failreason
                    if holdreason:
                        embed.add_field(name="Holdreason:", value=holdreason)
                    if failreason:
                        embed.add_field(name="Failreason:", value=failreason)
                    else:
                        embed.add_field(name="Error:", value="No reasons available")
                if '-v' in args:
                    streamurls = launch.vid_urls
                    if streamurls:
                        url = '\n'.join(streamurls)
                    else:
                        url = "No video available"
                    embed.add_field(name="Video", value=url)
                await ctx.send(embed=embed)
            else:
                await ctx.send("No launch with that ID.")
        else:
            await ctx.send("No ID provided.")

    @commands.command(aliases=['lana'])
    async def launchbyname(self, ctx, name, *args):
        """Tells information about launch with provided name.

        "str"     Name of the launch. (always first)
        -r        Includes holdreason and failreason.
        -v        Includes video URL.
        """
        if not can_answer(ctx):
            return
        for arg in args:
            if arg.startswith('-'):
                break
            else:
                name = name + ' ' + arg
        launches = launchlibrary.Launch.fetch(api, name=name)
        if launches:
            launch = launches[0]
            launchname = launch.name
            launchstatus = launch.get_status().description
            launchtime_tz = launch.net
            tz = launchtime_tz.tzname()
            launchtime = launchtime_tz.replace(tzinfo=None)
            embedcolor = discord.Colour(get_color(launch.agency.id))
            embed = discord.Embed(title=launchname, colour=embedcolor)
            embed.set_footer(text="ID: {0}".format(launch.id))
            embed.set_thumbnail(url=launch.rocket.image_url)
            embed.add_field(name=launch.net, value=launch.missions[0]['description'])
            if '-r' in args:
                holdreason = launch.holdreason
                failreason = launch.failreason
                if holdreason:
                    embed.add_field(name="Holdreason:", value=holdreason)
                if failreason:
                    embed.add_field(name="Failreason:", value=failreason)
                else:
                    embed.add_field(name="Error:", value="No reasons available")
            if '-v' in args:
                streamurls = launch.vid_urls
                if streamurls:
                    url = '\n'.join(streamurls)
                else:
                    url = "No video available"
                embed.add_field(name="Video", value=url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No launch found with that name.")

    @commands.command(aliases=['lina'])
    async def listbyname(self, ctx, name, *args):
        """Lists launches with provided name.

        -[int]    The number of launches listed. Default is 5, max 10.
        -s        Include launch status.
        """
        if not can_answer(ctx):
            return
        num = 5
        for arg in args:
            if arg.startswith('-'):
                break
            else:
                name = name + ' ' + arg
        for arg in args:
            if arg[1:].isdigit() and arg.startswith('-'):
                num = int(arg[1:])
        launches = launchlibrary.Launch.fetch(api, name=name)
        if launches:
            embedcolor = discord.Colour(get_color(launches[0].agency.id))
            msg = discord.Embed(title="Listing launches found with {0}:\n".format(name), colour=embedcolor)
            IDs = []
            for launch in launches[:num]:
                net = launch.net
                value = "Date: {0}".format(net.date())
                if net.time() != datetime(2000, 1, 1, 0).time(): # check if time is set to 0
                    value += ", Time: {0}".format(net.time())
                if "-s" in args:
                    value += ", Status: {0}".format(launch.get_status().name)
                if "-id" in args:
                    value += ", ID: {0}".format(launch.id)
                msg.add_field(name=launch.name, value=value, inline=False)
                IDs.append(launch.id)
            footer = 'IDs: ' + ', '.join(str(x) for x in IDs)
            msg.set_footer(text=footer)
            await ctx.send(embed=msg)
        else:
            msg = "No launches found with provided name."
            await send(ctx, msg, args)

    @commands.command(aliases=['lila', 'll'])
    async def listlaunches(self, ctx, *args):
        """Lists next launches.

        [int]     The number of launches listed. Default is 5, max is 10.
        """
        if not can_answer(ctx):
            return
        num = 5
        for arg in args:
            if arg.isdigit():
                num = int(arg)
        launches = launchlibrary.Launch.fetch(api, status=(1,2))[:num]
        embedcolor = discord.Colour(get_color(launches[0].agency.id))
        msg = discord.Embed(title="Listing next launches: ", colour=embedcolor)
        IDs = []
        for launch in launches:
            launchtime = launch.net
            utc = datetime.now(timezone.utc)
            T = chop_microseconds(launchtime - utc)
            if launch.status == 1:
                value = "T-: {0}".format(T)
            else:
                value = "T-: {0}; {1}".format(T, launch.get_status().name)
            msg.add_field(name=launch.name, value=value, inline=False)
            IDs.append(launch.id)
        footer = 'IDs: ' + ', '.join(str(x) for x in IDs)
        msg.set_footer(text=footer)
        await ctx.send(embed=msg)

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

class Rocketcommands(commands.Cog):
    """Commands related to rockets."""

    @commands.command(hidden=True)
    async def rocketbyname(self, ctx, name, *args):
        """Tells information about rocket with provided name.

        "str"     Name of the rocket. (always first)
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

    @commands.command(hidden=True)
    async def rocketbyid(self, ctx, *args):
        """Tells information about rocket with provided ID.

        [int]     ID of the rocket.
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

@bot.command(aliases=["die"], hidden=True)
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

@bot.command(hidden=True)
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


@bot.command()
async def git(ctx):
    """Gives link to the bot's github page."""
    if can_answer(ctx):
        msg = "https://github.com/Eerolz/launchbot"
        await ctx.send(msg)

@bot.event
async def on_ready():
    act_def = discord.Activity(type=discord.ActivityType.watching, name='Launch Library')
    if testchannelid:
        testchannel = bot.get_channel(testchannelid)
        await testchannel.send("Launchbot operational!")
    print("Launchbot operational!")

    launch = None
    launchids = ()
    alerttime = 30

    global alert_active
    if not alert_active:
        while 1:
            alert_active = True
            launchlist = launchlibrary.Launch.next(api, 3)
            if launchlist:
                launch = launchlist[0]
            if launch:
                launchtime = launch.net
                utc = datetime.now(timezone.utc)
                T = chop_microseconds(launchtime - utc)
                name = 'countdown: {0}'.format(T)
                act_T = discord.Activity(type=discord.ActivityType.watching, name=name)
                await bot.change_presence(activity=act_T)
                if T < timedelta(0):
                    check = 60*60
                    await bot.change_presence(activity=act_def)
                elif T < timedelta(minutes=5):
                    check = 5
                elif T < timedelta(hours=1):
                    check = round(T.total_seconds()/60)
                elif T < timedelta(hours=2):
                    check = 60
                elif T < timedelta(days=1):
                    check = 30*60
                else:
                    check = 60*60
                    await bot.change_presence(activity=act_def)
                for launch in launchlist:
                    launchtime = launch.net
                    utc = datetime.now(timezone.utc)
                    T = chop_microseconds(launchtime - utc)
                    if T < timedelta(minutes=alerttime) and launch.id not in launchids:
                        embed, msg2 = await launchalertformatter(launch)
                        for channelid in alertchannels:
                            channel = bot.get_channel(channelid)
                            if can_notify:
                                notifystr = notify('', channel)
                            else:
                                notifystr = "Notifying disabled.\n"
                            await channel.send(content=notifystr, embed=embed)
                            await channel.send(content=msg2)
                            launchids += (launch.id,)
                await asyncio.sleep(check)
            else:
                await bot.change_presence(activity=act_def)
                await asyncio.sleep(60*60)
    alert_active = False

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        print(error)

bot.run(TOKEN)
