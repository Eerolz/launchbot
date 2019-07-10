def reasons(msg, launch):
    holdreason = launch.holdreason
    failreason = launch.failreason
    if holdreason:
        msg += "Holdreason: {0}".format(holdreason)
    if holdreason and failreason:
        msg += ", "
    if failreason:
        msg += "Failreason: {0}".format(failreason)
    if holdreason or failreason:
        msg += "\n"
    else:
        msg += "No reasons available\n"
    return msg

def description(msg, launch):
    description = launch.missions[0]['description']
    msg += "\n{0}\n".format(description)
    return msg

def videourl(msg, launch):
    streamurls = launch.vid_urls
    if streamurls:
        streamurl = streamurls[0]
        msg += streamurl
    else:
        msg += "No video available"
    return msg

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
