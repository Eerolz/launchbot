import sqlite3
import configparser

configfile = "config.ini"
config = configparser.ConfigParser()
config.read(configfile)

authorities = config['BOT']['Authorities']
if authorities:
    authorities = authorities.split(',')
    authorities = list(map(int, authorities))
else:
    authorities = []

editors = config['BOT']['Editors']
if editors:
    editors = editors.split(',')
    editors = list(map(int, authorities))
else:
    editors = []

conn = sqlite3.connect('launcbot.db')
c = conn.cursor()


async def is_owner(ctx):
    return ctx.author.id in authorities

async def is_admin(ctx):
    return is_owner(ctx) or ctx.message.author.server_permissions.administrator

async def is_editor(ctx):
    return is_owner(ctx) or ctx.author.id in editors

async def can_answer(ctx):
    if not is_admin(ctx):
        with conn:
            cid = (ctx.channels.id,)
            c.execute("SELECT disabled FROM channels WHERE cid=?;", cid)
            return not c.fetchone()
    else:
        return True
