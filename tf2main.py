import json
import operator
import sqlite3
import random
from collections import Counter

import disnake
from disnake.ext import commands

intents = disnake.Intents.default()
intents.guilds = True
intents.presences = True

bot = commands.Bot(command_prefix='unused lol', intents=intents,
                   allowed_mentions=disnake.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True))
guilds = [770428394918641694]
rarities = ['Unique', 'Strange', 'Unusual', 'Collector\'s', 'Vintage', 'Normal', 'Decorated', 'Self-Made', 'VALVE',
            'noun', 'Community', 'Haunted', 'Genuine', 'Untradable', 'Uncraftable', 'Common', 'Mythic', 'Rare',
            'LEGENDARY', 'Uncued', 'Bliv']


@bot.slash_command(description='View and Equip Roles from your Role Inventory', name='roles', guild_ids=guilds)
async def roles(inter):
    await _roles(inter, type='Role')


@bot.slash_command(description='View and Equip Roles from your Role Icon Inventory', name='roleicons', guild_ids=guilds)
async def roles(inter):
    await _roles(inter, type='Role Icon')


async def _roles(inter, type):  # Lists a players' roles & role icons and allows them to choose between them.
    roles, roleIcons = get_user_roles(inter.author.id)
    guild = inter.guild

    true_items = []

    shortType = ''

    if type == 'Role':
        itemList = roles
        shortType = 'ro'
    else:
        itemList = roleIcons
        shortType = 'ri'

    for r in itemList:
        try:
            true_items.append(guild.get_role(r))
        except Exception as e:
            print(e)

    Menu = disnake.ui.Select()
    options = []
    for r in true_items:
        quality = random.choice(rarities)
        temp = disnake.SelectOption(label=r.name, value=f'{shortType}_{r.id}',
                                    description=f'Level {random.randint(0, 100)} {quality} Quality {r.name}!')
        options.append(temp)
    Menu.options = options
    Menu.custom_id = 'role_select'

    roleStrList = ''

    for i in true_items:
        roleStrList = f'{i.mention}\n{roleStrList}'
    embed = disnake.Embed(
        title=f'You currently own {len(true_items)} {type}{"s" if len(true_items) != 1 else ""}{":" if len(true_items) > 0 else "."}',
        description=roleStrList, color=0xD8B400)
    embed.set_footer(text=f"{type} are awarded for specific achivements. Use <command here> for more information.")
    if len(true_items) != 0:
        embed.set_footer(text=f'You can select a {type.lower()} to equip using the drop down menu below.')

    if len(true_items) > 0:
        message = await inter.response.send_message(components=[Menu], embed=embed, ephemeral=True)
    else:
        message = await inter.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(description='Assigns a role to a user.', name='giverole', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def addrole(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message("You can not assign the role @everyone!", ephemeral=True)
        return
    await inter.response.send_message(f"{member.mention} has been assigned the role {role.mention}!")
    database_update("add", user=member.id, role=role.id)


@bot.slash_command(description='Removes a role from a user.', name='removerole', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def removerole(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message("You can not remove @everyone from someone!", ephemeral=True)
        return
    await inter.response.send_message(f"{role.mention} was removed from {member.mention}!")
    database_update("remove", user=member.id, role=role.id)
    await member.remove_roles(role, reason=f'Role removed by {inter.author} ({inter.author.id})')


@bot.slash_command(description='Assigns a role to a user.', name='giveicon', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def addroleicon(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message("You can not assign the role @everyone!", ephemeral=True)
        return
    await inter.response.send_message(f"{member.mention} has been assigned the role icon {role.mention}!")
    database_update("add", user=member.id, roleIcon=role.id)


@bot.slash_command(description='Removes a role from a user.', name='removeicon', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def removeroleicon(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message("You can not remove @everyone from someone!", ephemeral=True)
        return
    await inter.response.send_message(f"{role.mention} has been removed from {member}!")
    database_update("remove", user=member.id, roleIcon=role.id)
    await member.remove_roles(role, reason=f'Role removed by {inter.author} ({inter.author.id})')

@bot.slash_command(description='Shows All Role Assignments', name='listroles', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def listall(inter):
    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    sql = '''SELECT * FROM roles'''
    cur.execute(sql)

    items = cur.fetchall()
    print(items)
    allRoles = []
    allIcons = []

    for i in items:
        usr, temp1, temp2 = i
        print(usr)
        member = await inter.guild.get_or_fetch_member(usr)
        if member is None:
            print(usr, member)
        else:
            temp1 = json.loads(temp1)
            temp2 = json.loads(temp2)
            for t1 in temp1:
                allRoles.append(t1)
            for t2 in temp2:
                allIcons.append(t2)

    roleCount = {}
    iconCount = {}

    for rl in allRoles:
        if rl not in roleCount:
            roleCount[rl] = 0
        roleCount[rl] += 1

    for ri in allIcons:
        if ri not in iconCount:
            iconCount[ri] = 0
        iconCount[ri] += 1

    roleCount = sorted(roleCount.items(), key=operator.itemgetter(1),reverse=True)
    iconCount = sorted(iconCount.items(), key=operator.itemgetter(1),reverse=True)

    roleStr = ''
    roleIconStr = ''
    roleClr = False
    for i in roleCount:
        temprole = inter.guild.get_role(i[0])
        roleStr = f'{roleStr}\n{temprole.mention}: **{i[1]}**'
        if not roleClr:
            color = temprole.color
            roleClr = True

    roleClr = False

    for i in iconCount:
        temprole = inter.guild.get_role(i[0])
        roleIconStr = f'{roleIconStr}\n{inter.guild.get_role(i[0]).mention}: **{i[1]}**'
        if not roleClr:
            color2 = temprole.color
            roleClr = True



    embed = disnake.Embed(title="Here are all the roles currently in use!", description=roleStr)
    embed.color = color
    embed.set_footer(text='NOTE: This only counts roles used by members still in the server.')
    embed2 = disnake.Embed(title="Here are all the roles currently in use!", description=roleIconStr)
    embed2.color = color2
    embed2.set_footer(text='NOTE: This only counts role icons used by members still in the server.')

    await inter.response.send_message(embeds=[embed, embed2])
    print(roleCount)
    print(iconCount)



@bot.listen("on_dropdown")
async def on_role_select(inter):
    if inter.data.custom_id == 'role_select':
        raw_id = inter.data.values[0]
        role_id = int(raw_id[3:])
        type = raw_id[:2]
        print(role_id, type)

        if type == 'ro':
            type = 'role'
        else:
            type = 'roleIcon'

        role = inter.guild.get_role(role_id)
        member = inter.author

        roleList = []

        roleIDs, roleIconIDs = get_user_roles(member.id)
        true_roles = []

        if type == 'role':
            true_roles = roleIDs
        else:
            true_roles = roleIconIDs

    for r in true_roles:
        roleList.append(inter.guild.get_role(r))

    try:
        roleList.remove(role)
    except Exception as e:
        await inter.response.send_message(embed=disnake.Embed(title="Invalid Role",
                                                              description="The role you selected either does not exist or has been removed from your inventory.",
                                                              color=0x0e0e0e), ephemeral=True)
        return

    await member.remove_roles(*roleList, reason=f'Role Assignment by {member.name}')
    await member.add_roles(role, reason=f'Role Assignment by {member.name}')

    embed = disnake.Embed(title='Role Selected',
                          description=f'You have equipped the role {role.mention} from your inventory.',
                          color=role.color)
    await inter.response.send_message(embed=embed, ephemeral=True)


def add_user_to_database(user):
    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    blank = json.dumps([])

    sql = '''INSERT INTO roles(user, role, roleicon) VALUES(?, ?, ?)'''  # Adds new user, default has no roles.
    cur.execute(sql, [user, blank, blank])
    conn.commit()


def get_user_roles(user):
    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    sql = '''SELECT role, roleicon FROM roles WHERE user IS ?'''
    cur.execute(sql, [user])  # Gets all roles & role icons from the user.

    item = cur.fetchone()
    if item:
        print(f'Found {item}')
    else:
        add_user_to_database(user)
        get_user_roles(user)

    # user_roles = json.load()
    roles_str, roleIcons_str = item
    roles, roleIcons = json.loads(roles_str), json.loads(roleIcons_str)

    return roles, roleIcons

def database_update(action, user, role=None, roleIcon=None):
    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    sql = '''SELECT role, roleicon FROM roles WHERE user IS ?'''
    cur.execute(sql, [user])  # Gets all roles & role icons from the user.

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

@bot.listen()
async def on_slash_command_error(ctx, error):
    if isinstance(error, disnake.ext.commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command!", ephemeral=True)
        return

    await ctx.send(f"Unknown Error:\n{error}\nPlease contact OblivionCreator#9905 for assistance or report an issue on the GitHub page at https://bliv.red/rolermobster")
    print(error)

bot.run(open('token.txt', 'r').read())
