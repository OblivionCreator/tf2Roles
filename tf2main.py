import json
import operator
import sqlite3
import random
import asyncio
import disnake
from disnake.ext import commands

intents = disnake.Intents.default()
intents.guilds = True
intents.presences = True

bot = commands.Bot(command_prefix='unused lol', intents=intents,
                   allowed_mentions=disnake.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True))
guilds = [770428394918641694, 296802696243970049]
rarities = ['Unique', 'Strange', 'Unusual', 'Collector\'s', 'Vintage', 'Normal', 'Decorated', 'Self-Made', 'VALVE',
            'noun', 'Community', 'Haunted', 'Genuine', 'Untradeable', 'Uncraftable', 'Common', 'Mythic', 'Rare',
            'LEGENDARY', 'Uncued', 'Bliv']


@bot.slash_command(description='Allows you to manage your active role, or view the roles of other users.', name='roles', guild_ids=guilds)
async def roles(inter, member:disnake.Member=None):
    await _roles(inter, type='Role', user=member)


@bot.slash_command(description='Allows you to manage your active role icon, or view the role icons of other users.', name='roleicons', guild_ids=guilds)
async def roleicons(inter, member:disnake.Member=None):
    await _roles(inter, type='Role Icon', user=member)


async def _roles(inter, type, isBlacklist=False, user=False):  # Lists a players' roles & role icons and allows them to choose between them.
    if isBlacklist:
        id = 9
    elif user:
        id = user.id
        await inter.response.defer(ephemeral=True)
    else:
        id = inter.author.id
        await inter.response.defer(ephemeral=True)
    roles, roleIcons = get_user_roles(id)
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

    if not isBlacklist and not user:
        Menu = disnake.ui.Select()
        options = []
        for r in true_items:
            quality = random.choice(rarities)
            level = random.randint(0, 100)
            temp = disnake.SelectOption(label=r.name, value=f'{shortType}_{r.id}',
                                        description=f'Level {level} {quality} Quality {r.name}!')
            options.append(temp)
        Menu.options = options
        Menu.custom_id = 'role_select'
    else:
        Menu = None

    roleStrList = ''

    for i in true_items:
        roleStrList = f'{i.mention}\n{roleStrList}'
    embed = disnake.Embed(
        title=f'{"There are currently"if isBlacklist else f"{user.name} currently has" if user else "You currently own"} {len(true_items)}{" Blacklisted" if isBlacklist else ""} {type}{"s" if len(true_items) != 1 else ""}{":" if len(true_items) > 0 else "."}',
        description=roleStrList, color=0xD8B400)
    if not isBlacklist:
        embed.set_footer(text=f"{type}s are awarded for specific achivements. Use <command here> for more information.")
    if len(true_items) != 0 and not isBlacklist and not user:
        embed.set_footer(text=f'You can select a {type.lower()} to equip using the drop down menu below.')

    if isBlacklist:
        return embed
    elif len(true_items) > 0 and not user:
        message = await inter.edit_original_message(components=[Menu], embed=embed)
    else:
        message = await inter.edit_original_message(embed=embed)


@bot.slash_command(description='Assigns a role to a user.', name='giverole', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def addrole(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message("You can not assign the role @everyone!", ephemeral=True)
        return

    bl_role, trash = get_user_roles(9)
    if role.id in bl_role:
        await inter.response.send_message(f"{role.mention} is in the blacklist and may not be given out!\nThis request has been logged.", ephemeral=True)
        return

    await inter.response.send_message(f"{member.mention} has been given the role {role.mention}!\nYou can equip your new role by doing `/roles`.")
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

    trash, bl_role = get_user_roles(9)
    if role.id in bl_role:
        await inter.response.send_message(f"{role.mention} is in the blacklist and may not be given out!\nThis request has been logged.", ephemeral=True)
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
async def listall(inter, role:disnake.Role=None):
    if role:
        return await list_specific_role(inter, role)

    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    sql = '''SELECT * FROM roles'''
    cur.execute(sql)

    items = cur.fetchall()
    allRoles = []
    allIcons = []

    for i in items:
        usr, temp1, temp2 = i
        member = await inter.guild.get_or_fetch_member(usr)
        if member is None:
            pass
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

    roleCount = sorted(roleCount.items(), key=operator.itemgetter(1), reverse=True)
    iconCount = sorted(iconCount.items(), key=operator.itemgetter(1), reverse=True)

    color = 0x000000
    color2 = 0x000000

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


async def list_specific_role(inter, role):
    await inter.response.defer()
    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    roleID = role.id

    sql = f'''SELECT * FROM roles WHERE role LIKE '%{roleID}%' OR roleicon LIKE '%{roleID}%' '''
    cur.execute(sql)

    items = cur.fetchall()
    print(items)
    userList = []
    if len(items) > 0:
        for i in items:
            user, trash1, trash2 = i
            userObj = await inter.guild.get_or_fetch_member(user)
            #print(userObj, user)
            if userObj:
                userList.append(userObj)
    allUserStr = ''
    if len(userList) > 0:
        for au in userList:
            allUserStr = f'{allUserStr}\n{au.mention}'
    else:
        allUserStr = "Nobody has this role!"
    embed = disnake.Embed(title=f'Everyone who has the Role {role.name}:', description=allUserStr, color=role.color)
    await inter.edit_original_message(embed=embed)

@bot.slash_command(name='dongulate', description='Adds all valid roles to a user.', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def dongulate(inter, user: disnake.User):
    roleIDs, roleIconIDs = get_user_roles(0)
    roles_to_add = []
    roleIcons_to_add = []

    for r in user.roles:
        if r.id in roleIDs:
            roles_to_add.append(r)
            database_update('add', user.id, role=r.id)
        if r.id in roleIconIDs:
            roleIcons_to_add.append(r)
            database_update('add', user.id, roleIcon=r.id)


    await user.remove_roles(*roles_to_add, reason='All valid roles added to user inventory.')
    await user.remove_roles(*roleIcons_to_add, reason='All valid role icons added to user inventory.')
    await inter.response.send_message(f"All valid roles have been assigned to {user.mention}")

@bot.slash_command(name='blacklist', description='Adds a role to the blacklist, forbidding it from being assigned.', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def blacklist(inter, role: disnake.Role):
    roleIDs, roleIconIDs = get_user_roles(9)
    roleA, roleIconA = get_user_roles(0)
    if role.id in roleIDs or role.id in roleIconIDs:
        database_update('remove', 9, role=role.id)
        await inter.response.send_message(content=f"{role.name} has been removed from the Blacklisted Roles", ephemeral=True)
    else:
        database_update('add', 9, role=role.id)
        await inter.response.send_message(f"{role.name} has been added to the Blacklisted Roles", ephemeral=True)
        if role.id in roleA:
            database_update("remove", 0, role=role.id)
        elif role.id in roleIconA:
            database_update("remove", 0, role=role.id)

@bot.slash_command(name='assignrole', description='Adds or removes a role from the Dongulatable roles.', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def assign_role(inter, role: disnake.Role):
    roleIDs, trash = get_user_roles(0)
    bl_r, trash = get_user_roles(9)
    if role.id in bl_r:
        await inter.response.send_message(content=f"{role.name} is blacklisted and may not be assigned.",
                                          ephemeral=True)
        return

    if role.id in roleIDs:
        database_update('remove', 0, role=role.id)
        await inter.response.send_message(content=f"{role.name} has been removed from the Dongulatable Roles", ephemeral=True)
    else:
        database_update('add', 0, role=role.id)
        await inter.response.send_message(f"{role.name} has been added to the Dongulatable Roles", ephemeral=True)

@bot.slash_command(name='viewblacklist', description='Lists all blacklisted roles and role icons.', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def vw_bl(inter):
    await inter.response.defer()
    embed1 = await _roles(inter, 'Role', isBlacklist = True)
    embed2 = await _roles(inter, 'RoleIcon', isBlacklist = True)
    await inter.edit_original_message(embeds=[embed1,embed2])

@bot.slash_command(name='assignroleicon', description='Adds or removes a role from the Dongulatable roles.', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def assign_role_icon(inter, role:disnake.Role):
    trash, roleIconIDs = get_user_roles(0)
    bl_r, trash = get_user_roles(9)
    if role.id in bl_r:
        await inter.response.send_message(content=f"{role.name} is blacklisted and may not be assigned.",
                                          ephemeral=True)
        return
    if role.id in roleIconIDs:
        database_update('remove', 0, roleIcon=role.id)
        await inter.response.send_message(content=f"{role.name} has been removed from the Dongulatable Role Icons", ephemeral=True)
    else:
        database_update('add', 0, roleIcon=role.id)
        await inter.response.send_message(f"{role.name} has been added to the Dongulatable Role Icons", ephemeral=True)

@bot.listen("on_dropdown")
async def on_role_select(inter):

    if inter.data.custom_id == 'role_select':
        raw_id = inter.data.values[0]
        role_id = int(raw_id[3:])
        type = raw_id[:2]

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
        await inter.send(embed=disnake.Embed(title="Invalid Role",
                                                              description="The role you selected either does not exist or has been removed from your inventory.",
                                                              color=0x0e0e0e), ephemeral=True)
        return


    try:
        await member.add_roles(role, reason=f'Role Assignment by {member.name}')
    except disnake.Forbidden as e:
        await inter.response.send_message("The bot encountered an error assigning you the role. This is likely due to the bot having incorrect permissions to assign the role requested.\nPlease contact a member of staff for assistance and use /roles to show them what roles you currently own.", ephemeral=True)
        return

    try:
        await member.remove_roles(*roleList, reason=f'Role Assignment by {member.name}')
    except disnake.Forbidden as e:
        await inter.response.send_message("The bot encountered an error removing your existing roles. This is likely due to the bot not having permissions to remove a role in your inventory.\nPlease contact a member of staff for assistance and use /roles to show them what roles you currently own.", ephemeral=True)
        return

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


def get_user_roles(user, skip=False):
    if user == 9:
        skip=True

    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    sql = '''SELECT role, roleicon FROM roles WHERE user IS ?'''
    cur.execute(sql, [user])  # Gets all roles & role icons from the user.

    item = cur.fetchone()
    if not item:
        add_user_to_database(user)
        return get_user_roles(user)


    # user_roles = json.load()
    roles_str, roleIcons_str = item
    roles, roleIcons = json.loads(roles_str), json.loads(roleIcons_str)

    if not skip:
        bl, trash = get_user_roles(9)

        for i in roles:
            if i in bl:
                database_update('remove', user, role=i)
                roles.remove(i)
        for ix in roleIcons:
            if ix in bl:
                database_update('remove', user, role=ix)
                roleIcons.remove(ix)

        bl, trash = get_user_roles(9, skip=True)
        to_blacklist = False
        for i in roles:
            if i in bl:
                to_blacklist = True
        for ix in roleIcons:
            if ix in bl:
                to_blacklist = True

        if to_blacklist:
            database_update("none", user)


    return roles, roleIcons


def database_update(action, user, role=None, roleIcon=None):

    conn = sqlite3.connect('roles.db')
    cur = conn.cursor()

    sql = '''SELECT role, roleicon FROM roles WHERE user IS ?'''
    cur.execute(sql, [user])  # Gets all roles & role icons from the user.

    roles, roleIcons = get_user_roles(user, skip=True)

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

    await ctx.send(
        f"Unknown Error:\n{error}\nPlease contact OblivionCreator#9905 for assistance or report an issue on the GitHub page at https://bliv.red/rolermobster")
    print(error)


bot.run(open('token.txt', 'r').read())
