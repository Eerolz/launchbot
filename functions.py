from datetime import datetime, timezone, timedelta

def reasons(embed, launch):
    holdreason = launch.holdreason
    failreason = launch.failreason
    if holdreason:
        embed.add_field(name="Holdreason", value=holdreason)
    if failreason:
        embed.add_field(name="Failreason", value=failreason)
    if not (holdreason or failreason):
        embed.add_field(name="Error", value="No reasons available")
    return embed

def time_description(embed, launch):
    launchtime_tz = launch.net
    tz = launchtime_tz.tzname()
    launchtime = launchtime_tz.replace(tzinfo=None)
    title = str(launchtime) + ' ' + tz
    if launch.missions:
        description = launch.missions[0]['description']
        if len(description) > 1000:
            embed.add_field(name=title, value=description[:997]+'...')
        else:
            embed.add_field(name=title, value=description)
    else:
        embed.add_field(name=title, value="No description available.")
    return embed

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)


def T_minus(launch):
    launchtime = launch.net
    utc = datetime.now(timezone.utc)
    delta = chop_microseconds(launchtime - utc)
    return delta - timedelta(microseconds=delta.microseconds)


def videourls(embed, launch):
    streamurls = launch.vid_urls
    if streamurls:
        url = '\n'.join(streamurls)
    else:
        url = "No video available"
    embed.add_field(name="Video", value=url)
    return embed

def id(msg, obj):
    id = obj.id
    msg += "ID: {0}\n".format(id)
    return msg

def familyid(msg, rocket):
    id = rocket.family.id
    msg += "Family ID: {0}\n".format(id)
    return msg

def agencyid(msg, rocket):
    id = rocket.family.agencies
    msg += "Agency ID: {0}\n".format(id)
    return msg

def padids(msg, rocket):
    id = rocket.default_pads
    msg += "Default pad IDs: {0}\n".format(id)
    return msg

def rocketwikiurl(msg, rocket):
    url = rocket.wiki_url
    msg += "{0}\n".format(url)
    return msg

def notify(msg, ctx):
    roles = ctx.guild.roles
    launchrole = None
    for role in roles:
        if role.name.lower() == 'launch notify':
            launchrole = role
    if launchrole:
        msg += '{0}\n'.format(launchrole.mention)
    else:
        msg += 'No launch notify role found.\n'
    return msg

def timelink(time):
    time = time.replace(tzinfo=None)
    hours = time.hour
    minutes = time.minute
    convertlink = 'https://www.thetimezoneconverter.com/?t={0}%3A{1}&tz=UTC'.format(hours, minutes)
    text = '[{0}]({1})'.format(time, convertlink)
    return text
