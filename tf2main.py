import configparser
import json
import sqlite3
import random
import disnake
from disnake.ext import commands, tasks
from configparser import ConfigParser
import os

intents = disnake.Intents.default()
intents.guilds = True
intents.presences = True
intents.members = True

try:
    masterRoles: list = json.load(open('config/parents.json'))
except FileNotFoundError:
    masterRoles: list = []
    json.dump(masterRoles, open('config/parents.json', 'w'))

# Create config/roles.db Database if it doesn't exist.
# Checks for the file

if not os.path.exists('config/roles.db'):
    conn = sqlite3.connect('config/roles.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE "roles" (
"user"	INTEGER NOT NULL UNIQUE,
"role"	INTEGER,
"roleicon"	INTEGER,
PRIMARY KEY("user"))''')
    conn.commit()
    conn.close()

default_role = 1099102181606555699

activity = disnake.Game(name="Managing Roles since 1999!")

bot = commands.InteractionBot(intents=intents,
                              allowed_mentions=disnake.AllowedMentions(everyone=False, users=True, roles=False,
                                                                       replied_user=True), activity=activity)
guilds = [770428394918641694, 296802696243970049, 1098819405321875571, 756193219737288836]


def getLang(inter, section, line):
    language = inter.locale

    languages = {
        'en-US': "translation/lang_en.ini",
        'en-GB': "translation/lang_en.ini",
    }

    if language in languages:
        file = languages[language]
    else:
        file = languages['en-US']

    lang = ConfigParser()
    lang.read(file, encoding='utf-8')
    try:
        lineStr = lang.get(section, line)
    except configparser.NoOptionError:
        file = languages['en-US']
        lang.read(file, encoding='utf-8')
        lineStr = lang.get(section, line)
    return lineStr


@bot.user_command(name='View Roles', guild_ids=guilds)
async def view_role_context(inter):
    await _roles(inter, role_type='Role', user=inter.target)


@bot.slash_command(name='add_parent', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def add_parent(inter, parent: disnake.Role, child: disnake.Role):
    global masterRoles

    if [parent.id, child.id] in masterRoles:
        inter.response.send_message(f"Role {parent.mention} already parents {child.mention}", ephemeral=True)
        return

    if [child.id, parent.id] in masterRoles:
        inter.response.send_message(
            f"Role {child.mention} parents {parent.mention}! Doing this would cause an infinite loop! Please remove the parenting first.",
            ephemeral=True)
        return

    masterRoles.append([parent.id, child.id])
    with open('config/parents.json', 'w') as f:
        json.dump(masterRoles, f)
    inter.response.send_message(f"Role {parent.mention} now parents {child.mention}", ephemeral=True)


@bot.slash_command(name='remove_parent', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def remove_parent(inter, parent: disnake.Role, child: disnake.Role):
    global masterRoles

    if [parent.id, child.id] not in masterRoles:
        inter.response.send_message(f"Role {parent.mention} does not parent {child.mention}", ephemeral=True)
        return

    masterRoles.remove([parent.id, child.id])
    with open('config/parents.json', 'w') as f:
        json.dump(masterRoles, f)
    inter.response.send_message(f"Role {parent.mention} no longer parents {child.mention}", ephemeral=True)


@bot.user_command(name='View Role Icons', guild_ids=guilds)
async def view_roleicon_context(inter):
    await _roles(inter, role_type='Icon', user=inter.target)


@bot.slash_command(description='Allows you to manage your active roles, or view the roles of other users.',
                   name='roles',
                   guild_ids=guilds)
async def roles(inter, member: disnake.Member = None, page: int = 1):
    await _roles(inter, role_type='Role', user=member, page=page)


async def _roles(inter: disnake.Interaction, role_type, returnEmbed=False,
                 user=False, page=1,
                 defer=True,
                 show_header=True):  # Lists a players' roles & role icons and allows them to choose between them.

    global default_role

    if page < 1:
        page = 1

    if not returnEmbed and defer:
        try:
            await inter.response.defer(ephemeral=True)
        except Exception:
            pass

    if user:

        if isinstance(user, int):
            id = user
        else:
            id = user.id
            if id == inter.author.id:
                user = False
    else:
        id = inter.author.id
    roles, roleIcons = get_user_roles(id)
    guild = inter.guild

    true_roles = []
    true_icons = []
    shortType = 'ro'

    if inter.guild.id == 296802696243970049:
        default_role = 831865797545951232
    elif inter.guild.id == 1098819405321875571:
        default_role = 1099102181606555699
    else:
        pass

    role_def = guild.get_role(default_role)
    if role_def:
        true_icons.append(guild.get_role(default_role))

    for r in roles:
        try:
            role = guild.get_role(r)
            if role is None:
                database_update('remove', id, role=r)
            else:
                true_roles.append(role)
        except Exception as e:
            print(e)

    for r in roleIcons:
        try:
            role = guild.get_role(r)
            if role is None:
                database_update('remove', id, roleIcon=r)
            else:
                true_icons.append(role)
        except Exception as e:
            print(e)

    if page - 1 > (len(true_roles)) / 25 or page - 1 > (len(true_roles)) / 25:
        page = 1

    true_roles.sort(reverse=True)
    true_icons.sort(reverse=True)
    true_roles_shortened = true_roles[(page - 1) * 25:(page * 25)]
    true_icons_shortened = true_icons[(page - 1) * 25:(page * 25)]

    aList = []

    if not returnEmbed and not user:
        rarities = getLang(inter, 'Translation', 'RARITY_LIST').split(', ')

        if len(true_roles_shortened) > 0:
            Menu1 = disnake.ui.Select()
            role_options = []
            for r in true_roles_shortened:
                random.seed(f"{r.name}{inter.author.id}")
                quality = random.choice(rarities)
                level = random.randint(0, 100)
                temp = disnake.SelectOption(label=r.name, value=f'ro_{r.id}',
                                            description=getLang(inter, 'Translation', 'ITEM_RARITY').format(level,
                                                                                                            quality,
                                                                                                            r.name))
                role_options.append(temp)
            Menu1.options = role_options
            Menu1.placeholder = "Select a Role!"
            Menu1.custom_id = 'role_select'
            aList.append(Menu1)

        if len(true_icons_shortened) > 0:
            Menu2 = disnake.ui.Select()
            Menu2.placeholder = "Select a Role Icon!"
            icon_options = []
            for r in true_icons_shortened:
                random.seed(f"{r.name}{inter.author.id}")
                quality = random.choice(rarities)
                level = random.randint(0, 100)
                temp = disnake.SelectOption(label=r.name, value=f'ro_{r.id}',
                                            description=getLang(inter, 'Translation', 'ITEM_RARITY').format(level,
                                                                                                            quality,
                                                                                                            r.name))
                icon_options.append(temp)
            Menu2.options = icon_options
            Menu2.custom_id = 'icon_select'
            aList.append(Menu2)

    roleStrList = ''
    iconStrList = ''
    PageDown = None
    PageUp = None

    true_length = len(true_roles)
    true_length_2 = len(true_icons)
    if len(true_icons) > 0:
        if true_icons[0] is None:
            true_icons.pop(0)
        elif true_icons[0].id == default_role:
            true_length_2 = len(true_icons) - 1

    if len(true_icons) == 1 or id == 9:
        true_icons = true_icons[1:]

    for r in true_roles_shortened:
        roleStrList = f'{roleStrList}\n{r.mention}'
    for i in true_icons_shortened:
        iconStrList = f'{iconStrList}\n{i.mention}'

    if (len(true_roles) > len(true_roles_shortened) or len(true_icons) > len(
            true_icons_shortened)) and user == inter.author.id:
        roleStrList = f'{roleStrList}\n**({((page - 1) * 25) + 1}-{(((page - 1) * 25) + 1) + len(true_roles_shortened) - 1})**'
        iconStrList = f'{iconStrList}\n**({((page - 1) * 25) + 1}-{(((page - 1) * 25) + 1) + len(true_icons_shortened) - 1})**'

        if (len(true_roles) > 1 and len(true_roles_shortened) > 1 and (
                true_roles[-1] == true_roles_shortened[-1]) and len(true_roles) > 25) or (
                len(true_icons) > 25 and len(true_icons_shortened) > 1 and (
                true_icons[-1] == true_icons_shortened[-1])):
            pageDown = disnake.ui.Button(label='<-', custom_id=f'{shortType}_{page - 1}',
                                         style=disnake.ButtonStyle.blurple)
            aList.append(pageDown)
        if (len(true_roles) > 1 and len(true_roles_shortened) > 1 and (
                true_roles[0] == true_roles_shortened[0] and len(true_roles) > 25)) or (
                len(true_icons) > 25 and len(true_icons_shortened) > 1 and (true_icons[0] == true_icons_shortened[0])):
            pageUp = disnake.ui.Button(label='->', custom_id=f'{shortType}_{page + 1}',
                                       style=disnake.ButtonStyle.blurple)
            aList.append(pageUp)

    if true_length != 1:
        type_plural = getLang(inter, section='Translation', line=f'{role_type.upper()}_PLURAL')
    else:
        type_plural = getLang(inter, section='Translation', line=f'{role_type.upper()}')

    if id == 9:
        embTitle = getLang(inter, section='Translation', line='ROLES_LIST_BLACKLIST').format(true_length,
                                                                                             type_plural)
    elif user and not isinstance(user, int):
        embTitle = getLang(inter, section='Translation', line='ROLES_LIST_USER').format(user.name, true_length,
                                                                                        type_plural)
    else:
        if show_header:
            embTitle = f"You currently own {true_length} Roles and {true_length_2} Role Icons"
        else:
            embTitle = '⠀'

    embed = disnake.Embed(title=embTitle, description="", color=0xD8B400)
    embed.add_field(name="Roles", value=roleStrList, inline=True)
    embed.add_field(name="Role Icons", value=iconStrList, inline=True)
    if not returnEmbed:
        embed.set_footer(text="Roles and Role Icons are awarded for specific achievements.")
    if len(true_roles) != 0 and not returnEmbed and not user:
        embed.set_footer(text=getLang(inter, section='Translation', line='ROLE_FOOTER_DROPDOWN').format(
            getLang(inter, section='Translation', line=f'{role_type.upper()}')))

    if returnEmbed:
        return embed, aList
    else:
        message = await inter.edit_original_message(components=aList, embed=embed)


@bot.slash_command(description='Assigns a role to a user.', name='giverole', guild_ids=guilds, aliases=['r'])
@commands.has_permissions(manage_roles=True)
async def addrole(inter, member: disnake.abc.User, role: disnake.abc.Role):
    global masterRoles

    roles_to_add = [role.id]
    if role.name == '@everyone':
        await inter.response.send_message(getLang(inter, section='Translation', line=f'GIVE_ROLE_FAILED_EVERYONE'),
                                          ephemeral=True)
        return

    bl_role, trash = get_user_roles(9)
    if role.id in bl_role:
        await inter.response.send_message(getLang(inter, section='Translation', line=f'GIVE_ROLE_FAILED_BLACKLIST'),
                                          ephemeral=True),
        return

    user_roles, trash = get_user_roles(member.id)
    if role.id in user_roles:
        await inter.response.send_message(getLang(inter, section='Translation', line=f'GIVE_ROLE_FAILED_EXISTS')
                                          .format(member.mention, role.mention),
                                          ephemeral=True),
        return

    await inter.response.send_message(
        getLang(inter, section='Translation', line=f'GIVE_ROLE_SUCCESS').format(member.mention, role.mention))

    for i in roles_to_add:
        for ix in masterRoles:
            pri, sec = ix
            if pri == i:
                roles_to_add.append(sec)

    for x in roles_to_add:
        database_update("add", user=member.id, role=x)


@bot.slash_command(description='Removes a role from a user.', name='removerole', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def removerole(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message(getLang(inter, section='Translation', line=f'REMOVE_ROLE_FAILED_EVERYONE'),
                                          ephemeral=True)
        return

    user_roles, trash = get_user_roles(member.id)
    if role.id not in user_roles:
        await inter.response.send_message(getLang(inter, section='Translation', line=f'REMOVE_ROLE_FAILED_MISSING')
                                          .format(member.mention, role.mention),
                                          ephemeral=True)
        return

    if inter.locale == 'ko':
        tempF = getLang(inter, section='Translation', line='REMOVE_ROLE_SUCCESS').format(member.mention, role.mention)
    else:
        tempF = getLang(inter, section='Translation', line='REMOVE_ROLE_SUCCESS').format(role.mention, member.mention)
    await inter.response.send_message(tempF)
    database_update("remove", user=member.id, role=role.id)
    await member.remove_roles(role, reason=f'Role removed by {inter.author} ({inter.author.id})')


@bot.slash_command(description='Gives an icon to a user.', name='giveicon', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def addroleicon(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message(getLang(inter, section='Translation', line=f'GIVE_ROLE_FAILED_EVERYONE'),
                                          ephemeral=True)
        return

    trash, bl_role = get_user_roles(9)
    if role.id in bl_role:
        await inter.response.send_message(getLang(inter, section='Translation', line=f'GIVE_ROLE_FAILED_BLACKLIST'),
                                          ephemeral=True)
        return

    trash, user_icons = get_user_roles(member.id)
    if role.id in user_icons:
        await inter.response.send_message(getLang(inter, section='Translation', line=f'GIVE_ROLE_FAILED_EXISTS')
                                          .format(member.mention, role.mention),
                                          ephemeral=True),
        return

    await inter.response.send_message(
        getLang(inter, section='Translation', line=f'GIVE_ICON_SUCCESS').format(member.mention, role.mention))
    database_update("add", user=member.id, roleIcon=role.id)


@bot.slash_command(description='Removes an icon from a user.', name='removeicon', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def removeroleicon(inter, member: disnake.abc.User, role: disnake.abc.Role):
    if role.name == '@everyone':
        await inter.response.send_message(getLang(inter, section='Translation', line=f'REMOVE_ROLE_FAILED_EVERYONE'),
                                          ephemeral=True)
        return

    trash, user_icons = get_user_roles(member.id)
    if role.id not in user_icons:
        await inter.response.send_message(getLang(inter, section='Translation', line=f'REMOVE_ROLE_FAILED_MISSING')
                                          .format(member.mention, role.mention),
                                          ephemeral=True)
        return

    if inter.locale == 'ko':
        tempF = getLang(inter, section='Translation', line='REMOVE_ROLE_SUCCESS').format(member.mention, role.mention)
    else:
        tempF = getLang(inter, section='Translation', line='REMOVE_ROLE_SUCCESS').format(role.mention, member.mention)
    await inter.response.send_message(tempF)
    database_update("remove", user=member.id, roleIcon=role.id)
    await member.remove_roles(role, reason=f'Role removed by {inter.author} ({inter.author.id})')


@bot.slash_command(description='Shows All Role Assignments', name='listroles', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def listall(inter, role: disnake.Role = None):
    if role:
        return await list_specific_role(inter, role)

    await inter.response.defer()

    conn = sqlite3.connect('config/roles.db')
    cur = conn.cursor()

    sql = '''SELECT * FROM roles'''
    cur.execute(sql)

    items = cur.fetchall()
    allRoles = []
    allIcons = []
    user_count = 0

    sql2 = '''SELECT COUNT(*) FROM roles'''
    cur.execute(sql2)
    user_total, = cur.fetchone()

    guild_member_ids = [member.id for member in inter.guild.members]

    for i in items:
        user, temp1, temp2 = i
        if user in guild_member_ids:
            temp1 = json.loads(temp1)
            temp2 = json.loads(temp2)
            for t1 in temp1:
                allRoles.append(t1)
            for t2 in temp2:
                allIcons.append(t2)
            user_count += 1

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

    roleCount = sorted(roleCount.items(), key=lambda x: [x[1], inter.guild.get_role(x[0])], reverse=True)
    iconCount = sorted(iconCount.items(), key=lambda x: [x[1], inter.guild.get_role(x[0])], reverse=True)

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

    embed = disnake.Embed(title=getLang(inter, 'Translation', 'LIST_ALL_ROLES'), description=roleStr)
    embed.color = color
    embed.set_footer(text=getLang(inter, 'Translation', 'LIST_ALL_ROLES_FOOTER'))
    embed2 = disnake.Embed(title=getLang(inter, 'Translation', 'LIST_ALL_ICONS'), description=roleIconStr)
    embed2.color = color2
    embed2.set_footer(text=getLang(inter, 'Translation', 'LIST_ALL_ICONS_FOOTER').format(user_count, user_total))

    await inter.edit_original_message(embeds=[embed, embed2])


async def list_specific_role(inter, role):
    await inter.response.defer()
    conn = sqlite3.connect('config/roles.db')
    cur = conn.cursor()

    roleID = role.id

    sql = f'''SELECT * FROM roles WHERE role LIKE '%{roleID}%' '''
    cur.execute(sql)
    roleItems = cur.fetchall()

    sql2 = f'''SELECT * FROM roles WHERE roleicon LIKE '%{roleID}%' '''
    cur.execute(sql2)
    iconItems = cur.fetchall()

    userRoleList = []
    userIconList = []

    guild_member_ids = [member.id for member in inter.guild.members]

    for i in roleItems:
        user, trash1, trash2 = i
        if user in guild_member_ids:
            userObj = await inter.guild.get_or_fetch_member(user)
            userRoleList.append(userObj)

    for i in iconItems:
        user, trash1, trash2 = i
        if user in guild_member_ids:
            userObj = await inter.guild.get_or_fetch_member(user)
            userIconList.append(userObj)

    embeds = []

    allUserRoleStr = ''
    if len(userRoleList) > 0:
        for au in userRoleList:
            allUserRoleStr = f'{allUserRoleStr}\n{au.name} ({au.mention})'
            if len(allUserRoleStr) > 4000:
                allUserRoleStr = f'{allUserRoleStr}\n{getLang(inter, "Translation", "LIST_ALL_OVERFLOW").format((len(userRoleList) - userRoleList.index(au)))}'
                break
        embeds.append(disnake.Embed(title=getLang(inter, 'Translation', 'LIST_ROLE').format(role.name),
                                    description=allUserRoleStr,
                                    color=role.color))

    allUserIconStr = ''
    if len(userIconList) > 0:
        for au in userIconList:
            allUserIconStr = f'{allUserIconStr}\n{au.name} ({au.mention})'
            if len(allUserIconStr) > 4000:
                allUserIconStr = f'{allUserIconStr}\n{getLang(inter, "Translation", "LIST_ALL_OVERFLOW").format((len(userIconList) - userIconList.index(au)))}'
                break
        embeds.append(disnake.Embed(title=getLang(inter, 'Translation', 'LIST_ICON').format(role.name),
                                    description=allUserIconStr,
                                    color=role.color))

    if len(embeds) == 0:
        embeds.append(disnake.Embed(title=getLang(inter, 'Translation', 'LIST_ROLE').format(role.name),
                                    description=getLang(inter, 'Translation', 'LIST_ROLE_RETURN_NONE'),
                                    color=role.color))

    await inter.edit_original_message(embeds=embeds)


@bot.slash_command(name='store', description='Stores all your eligible roles & icons in your Roler Mobster Inventory')
async def store(inter):
    await dongulate(inter, user=inter.author)


@bot.slash_command(name='dongulate', description='Adds all valid roles to a user.', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def dongulate(inter, user: disnake.User):
    global masterRoles
    await inter.response.defer()
    roleIDs, roleIconIDs = get_user_roles(0)
    roles_to_add = []
    roleIcons_to_add = []

    userRoles = user.roles

    dupeRole = None

    for r in userRoles:

        if r.id == 538179836531834906:
            dupeRole = r
            r = inter.guild.get_role(538496816845553704)
        for i in masterRoles:
            pri, sec = i
            if pri == r.id:
                role = inter.guild.get_role(sec)
                if role not in userRoles:
                    database_update('add', user.id, role=role.id)

        if r.id in roleIDs:
            roles_to_add.append(r)
            database_update('add', user.id, role=r.id)
        if r.id in roleIconIDs:
            roleIcons_to_add.append(r)
            database_update('add', user.id, roleIcon=r.id)

    if dupeRole:
        roles_to_add.append(dupeRole)

    await user.remove_roles(*roles_to_add[1:], reason='All valid roles added to user inventory.')
    await user.remove_roles(*roleIcons_to_add[1:], reason='All valid role icons added to user inventory.')
    await inter.edit_original_message(content=getLang(inter, 'Translation', 'DONGULATE_SUCCESS').format(user.mention))


@bot.slash_command(name='blacklist', description='Adds a role to the blacklist, forbidding it from being assigned.',
                   guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def blacklist(inter, role: disnake.Role):
    roleIDs, roleIconIDs = get_user_roles(9)
    roleA, roleIconA = get_user_roles(0)
    if role.id in roleIDs or role.id in roleIconIDs:
        database_update('remove', 9, role=role.id)
        await inter.response.send_message(
            content=getLang(inter, 'Translation', 'BLACKLIST_REMOVE_SUCCESS').format(role.name),
            ephemeral=True)
    else:
        database_update('add', 9, role=role.id)
        await inter.response.send_message(getLang(inter, 'Translation', 'BLACKLIST_ADD_SUCCESS').format(role.name),
                                          ephemeral=True)
        if role.id in roleA:
            database_update("remove", 0, role=role.id)
        elif role.id in roleIconA:
            database_update("remove", 0, role=role.id)

@bot.slash_command(name='delete-role', description='Deletes a role from the database.', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def delete_role(inter, role: disnake.Role):
    # Selects all users with the role ID
    role_id = role.id

    conn = sqlite3.connect('config/roles.db')
    cur = conn.cursor()
    sql = f'''SELECT * FROM roles WHERE role LIKE ? OR roleicon LIKE ?'''
    cur.execute(sql, ('%' + str(role_id) + '%', '%' + str(role_id) + '%'))
    affected_users = cur.fetchall()
    for user in affected_users:
        user_id, role_ids, role_icons = user
        role_ids = json.loads(role_ids)
        role_icons = json.loads(role_icons)
        if role_id in role_ids:
            role_ids.remove(role_id)
        if role_id in role_icons:
            role_icons.remove(role_id)
        # The role is removed! Let's update their database entry.

        sql = f'''UPDATE roles SET role = ?, roleicon = ? WHERE user = ?'''
        cur.execute(sql, (json.dumps(role_ids), json.dumps(role_icons), user_id))
    conn.commit()
    conn.close()
    await inter.response.send_message(content=getLang(inter, 'Translation', 'DELETE_ROLE_SUCCESS').format(role.name, len(affected_users)))

@bot.slash_command(name='assignrole', description='Adds or removes a role from the Dongulatable roles.',
                   guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def assign_role(inter, role: disnake.Role):
    roleIDs, trash = get_user_roles(0)
    bl_r, trash = get_user_roles(9)
    if role.id in bl_r:
        await inter.response.send_message(
            content=getLang(inter, 'Translation', 'DONGULATE_ASSIGN_FAILED_BLACKLIST').format(role.name),
            ephemeral=True)
        return

    if role.id in roleIDs:
        database_update('remove', 0, role=role.id)
        await inter.response.send_message(
            content=getLang(inter, 'Translation', 'DONGULATE_ASSIGN_REMOVED_SUCCESS').format(role.name),
            ephemeral=True)
    else:
        database_update('add', 0, role=role.id)
        await inter.response.send_message(
            getLang(inter, 'Translation', 'DONGULATE_ASSIGN_ADDED_SUCCESS').format(role.name), ephemeral=True)


@bot.slash_command(name='viewblacklist', description='Lists all blacklisted roles and role icons.', guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def vw_bl(inter, page: int = 1):
    user = 9
    await inter.response.defer()
    embed1, components = await _roles(inter, 'Role', returnEmbed=True, user=user, page=page)
    await inter.edit_original_message(embeds=[embed1], components=components)


@bot.slash_command(name='show', description='Shows off your role inventory publicly!', guild_ids=guilds)
async def showoff(inter):
    await inter.response.defer()

    # get role list
    roles, icons = get_user_roles(inter.author.id)
    page = 1
    embeds = []
    role_count = len(roles)
    icon_count = len(icons)
    while role_count > 0 or icon_count > 0:
        temp1, temp2 = await _roles(inter, 'Role', returnEmbed=True, user=inter.author.id, page=page)
        embeds.append(temp1)
        role_count -= 25
        icon_count -= 25
        page += 1
    user = inter.author
    await inter.edit_original_message(embeds=embeds)


@bot.slash_command(name='assignicon', description='Adds or removes a role from the Dongulatable roles.',
                   guild_ids=guilds)
@commands.has_permissions(manage_roles=True)
async def assign_role_icon(inter, role: disnake.Role):
    trash, roleIconIDs = get_user_roles(0)
    bl_r, trash = get_user_roles(9)
    if role.id in bl_r:
        await inter.response.send_message(
            content=getLang(inter, 'Translation', 'DONGULATE_ASSIGN_FAILED_BLACKLIST').format(role.name),
            ephemeral=True)
        return
    if role.id in roleIconIDs:
        database_update('remove', 0, roleIcon=role.id)
        await inter.response.send_message(
            content=getLang(inter, 'Translation', 'DONGULATE_ASSIGN_REMOVED_SUCCESS_ICON').format(role.name),
            ephemeral=True)
    else:
        database_update('add', 0, roleIcon=role.id)
        await inter.response.send_message(
            getLang(inter, 'Translation', 'DONGULATE_ASSIGN_ADDED_SUCCESS_ICON').format(role.name), ephemeral=True)


@bot.listen("on_dropdown")
async def on_role_select(inter):
    await inter.response.defer(ephemeral=True)
    if inter.data.custom_id == 'role_select' or inter.data.custom_id == 'icon_select':
        raw_id = inter.data.values[0]
        role_id = int(raw_id[3:])
        type = raw_id[:2]

        if inter.data.custom_id == 'role_select':
            type = 'role'
        else:
            type = 'roleIcon'

        role = inter.guild.get_role(role_id)
        member = inter.author
        memberRoleIDs = [role.id for role in member.roles]

        roleList = []

        roleIDs, roleIconIDs = get_user_roles(member.id)
        true_roles = []

        if type == 'role':
            true_roles = roleIDs
        else:
            true_roles = roleIconIDs

    for r in true_roles:
        if r in memberRoleIDs:
            roleList.append(inter.guild.get_role(r))

    roleList.append(role)

    if role_id != default_role and role in roleList:
        try:
            roleList.remove(role)
        except Exception as e:
            await inter.send(embed=disnake.Embed(
                title=getLang(inter, 'Translation', 'EQUIP_ROLE_FAILED_BAD_ROLE_TITLE').format(role.name),
                description=getLang(inter, 'Translation', 'EQUIP_ROLE_FAILED_BAD_ROLE'),
                color=0x0e0e0e), ephemeral=True)
            return

    try:
        await member.add_roles(role, reason=f'Role Assignment by {member.name}')
    except disnake.Forbidden as e:
        await inter.followup.send(
            getLang(inter, 'Translation', 'EQUIP_ROLE_FAILED_ERROR_GENERIC'),
            ephemeral=True)
        return

    try:
        await member.remove_roles(*roleList, reason=f'Role Assignment by {member.name}')
    except disnake.Forbidden as e:
        await inter.followup.send(
            getLang(inter, 'Translation', 'REMOVE_ROLE_FAILED_ERROR_GENERIC'),
            ephemeral=True)
        return

    if role_id != default_role:
        embed = disnake.Embed(title='Role Selected',
                              description=getLang(inter, 'Translation', 'EQUIP_ROLE_SUCCESS').format(role.mention),
                              color=role.color)
    else:
        embed = disnake.Embed(title='Icon Removed',
                              description=getLang(inter, 'Translation', 'ICON_REMOVE_SUCCESS').format(role.mention),
                              color=role.color)
    await inter.followup.send(embed=embed, ephemeral=True)


@bot.slash_command(name='equipall',
                   description='Equips all of your roles at once. (If you have a lot of roles, this may take some time!)',
                   guilds_ids=guilds)
async def equipall(inter):
    await inter.response.defer(ephemeral=True)
    roles, icons = get_user_roles(inter.author.id)
    all_roles = roles + icons
    role_list = []

    for r in all_roles:
        if r not in [role.id for role in inter.author.roles]:
            role_list.append(inter.guild.get_role(r))
    try:
        await inter.author.add_roles(*role_list)
        await inter.edit_original_message(
            content=getLang(inter, 'Translation', 'EQUIP_ALL_ROLE_SUCCESS').format(len(all_roles)))
    except Exception as e:
        await inter.edit_original_message(content=getLang(inter, 'Translation', 'EQUIP_ALL_ROLE_FAILED_ERROR_GENERIC'))


@bot.listen("on_button_click")
async def on_page_click(inter):
    custom_id = inter.data.custom_id
    if custom_id[0:2] == 'ro':
        longvariablethatdoesnothing, pageNo = custom_id.split("_")
        await _roles(inter, role_type='Role', page=int(pageNo))
        if custom_id[0:2] == 'ri':
            longvariablethatdoesnothing, pageNo = custom_id.split("_")
            await _roles(inter, role_type='Icon', page=int(pageNo))


def add_user_to_database(user):
    conn = sqlite3.connect('config/roles.db')
    cur = conn.cursor()

    blank = json.dumps([])

    sql = '''INSERT INTO roles(user, role, roleicon) VALUES(?, ?, ?)'''  # Adds new user, default has no roles.
    cur.execute(sql, [user, blank, blank])
    conn.commit()


def get_user_roles(user, skip=False):
    if user == 9:
        skip = True

    conn = sqlite3.connect('config/roles.db')
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
    conn = sqlite3.connect('config/roles.db')
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


# @bot.listen()
# async def on_slash_command_error(ctx, error):
#     if isinstance(error, disnake.ext.commands.MissingPermissions):
#         await ctx.send(getLang(ctx, 'Translation', 'COMMAND_FAILED_BAD_PERMISSIONS'), ephemeral=True)
#         return
#     elif isinstance(error, disnake.ext.commands.CommandOnCooldown):
#         await ctx.send(getLang(ctx, 'Translation', 'COMMAND_FAILED_COOLDOWN'), ephemeral=True)
#         return
#     await ctx.send(
#         getLang(ctx, 'Translation', 'COMMAND_FAILED_UNKNOWN_ERROR').format(error))
#     print(error)

@tasks.loop(minutes=5)
async def changeStatus():
    await statusChanger()


async def statusChanger():
    status = disnake.Status.online

    from datetime import date

    flavor = ["Obsessed with roles, and abhors Chaos.", "Tasque Manager blocks the way!",
              "Tasque Manager makes a list of her roles for the next year. She only has one role.",
              "Tasque Manager is writing \"manage tasks\" next to every entry in her daily planner.",
              "Tasque Manager is straightening her whip with a hair straightener.",
              "Tasque Manager is making herself take priority over the roles.", "Smells like live wiring"]

    await bot.change_presence(activity=disnake.Game(random.choice(flavor)))


@bot.event
async def on_ready():
    changeStatus.start()


bot.run(open('config/token.txt', 'r').read())
