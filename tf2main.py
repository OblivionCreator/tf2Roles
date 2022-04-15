import json
import sqlite3
import random

import disnake
from disnake.ext import commands

intents = disnake.Intents.default()
bot = commands.Bot(command_prefix='unused lol', intents=intents, allowed_mentions= disnake.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True))
guilds = [770428394918641694]
rarities = ['Unique', 'Strange', 'Unusual', 'Collector\'s', 'Vintage', 'Normal', 'Decorated', 'Self-Made', 'VALVE', 'noun', 'Community', 'Haunted', 'Genuine', 'Untradable', 'Uncraftable', 'Common', 'Mythic', 'Rare', 'LEGENDARY', 'Uncued', 'Bliv']

@bot.slash_command(description='View and Equip Roles from your Role Inventory', name='roles', guild_ids=guilds)
async def roles(inter):
    await _roles(inter, type='Role')

@bot.slash_command(description='View and Equip Roles from your Role Icon Inventory', name='roleicons', guild_ids=guilds)
async def roles(inter):
    await _roles(inter, type='Role Icon')

async def _roles(inter, type): # Lists a players' roles & role icons and allows them to choose between them.
    roles, roleIcons = get_user_roles(inter.author.id)
    guild = inter.guild

    true_items = []

    if type == 'Role':
        itemList = roles
    else:
        itemList = roleIcons

    for r in itemList:
        try:
            true_items.append(guild.get_role(r))
        except Exception as e:
            print(e)

    Menu = disnake.ui.Select()
    options = []
    for r in true_items:

        quality = random.choice(rarities)
        temp = disnake.SelectOption(label = r.name, value = r.id, description=f'Level {random.randint(0,100)} {quality} Quality {r.name}!')
        options.append(temp)
    Menu.options = options

    roleStrList = ''

    for i in true_items:
        roleStrList = f'{i.mention}\n{roleStrList}'
    embed = disnake.Embed(title=f'You currently own {len(true_items)} {type}{"s" if len(true_items) != 1 else ""}{":" if len(true_items) > 0 else "."}', description=roleStrList, color=0xD8B400)
    embed.set_footer(text=f"{type} are awarded for specific achivements. Use <command here> for more information.")
    if len(true_items) != 0:
        embed.set_footer(text=f'You can select a {type.lower()} to equip using the drop down menu below.')

    if len(true_items) > 0:
        message = await inter.response.send_message(components=[Menu], embed=embed, ephemeral=True)
    else:
        message = await inter.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(description='Assigns a role to a user.', name='assign', guild_ids=guilds)
async def addrole(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message("You can not assign the role @everyone!", ephemeral=True)
        return
    await inter.response.send_message(f"{member.mention} has been assigned the role {role.mention}!")
    database_update("add", user=member.id, role=role.id)

async def removerole(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message("You can not remove @everyone from someone!", ephemeral=True)
        return
    await inter.response.send_message(f"{member.mention} has been assigned the role {role.mention}!")
    database_update("remove", user=member.id, role=role.id)

def add_user_to_database(user):
    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    blank = json.dumps([])

    sql = '''INSERT INTO roles(user, role, roleicon) VALUES(?, ?, ?)''' # Adds new user, default has no roles.
    cur.execute(sql, [user, blank, blank])
    conn.commit()

def get_user_roles(user):

    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    sql = '''SELECT role, roleicon FROM roles WHERE user IS ?'''
    cur.execute(sql, [user]) # Gets all roles & role icons from the user.

    item = cur.fetchone()
    if item:
        print(f'Found {item}')
    else:
        add_user_to_database(user)
        get_user_roles(user)

    #user_roles = json.load()
    roles_str, roleIcons_str = item
    roles, roleIcons = json.loads(roles_str), json.loads(roleIcons_str)

    return roles, roleIcons

def database_update(action, user, role = None, roleIcon = None):
    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    sql = '''SELECT role, roleicon FROM roles WHERE user IS ?'''
    cur.execute(sql, [user]) # Gets all roles & role icons from the user.

    roles, roleIcons = get_user_roles(user)

    if action == 'add':
        if role in roles or roleIcon in roleIcons:
            return 'User already has role!'
        if role:
            roles.append(role)
        if roleIcon:
            roleIcons.append(roleIcon)
    elif action == 'remove':
        if role:
            if role not in roles:
                return 'User does not have that role!'

            roles.remove(role)
        if roleIcon:
            if roleIcon not in roleIcons:
                return 'User does not have that role!'

            roleIcons.remove(roleIcon)
    else:
        return False

    sql2 = '''UPDATE roles SET role = ? WHERE user IS ?'''
    cur.execute(sql2, [json.dumps(roles), user])
    sql3 = '''UPDATE roles SET roleicon = ? WHERE user IS ? '''
    cur.execute(sql3, [json.dumps(roleIcons), user])
    conn.commit()

bot.run(open('token.txt', 'r').read())
