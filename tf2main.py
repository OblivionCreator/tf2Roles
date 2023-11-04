import configparser
import json
import sqlite3
import random
import disnake
from disnake.ext import commands
from configparser import ConfigParser

intents = disnake.Intents.default()
intents.guilds = True
intents.presences = True
intents.members = True

masterRoles = [
    (298698700719521795, 298698201270059009),  # Rhythm Maestro -> Sushi Maestro
    (409552655623389185, 409551428814635008),  # Rhythm Master -> Sushi Master
    (966299552112062494, 409551428814635008),  # Rhythm Completionist -> Sushi Master
    (819428632447287296, 973061504180035644),  # Café Champion -> Café Addict
    (973061504180035644, 517143533853868074),  # Café Addict -> Café Regular
    (517143533853868074, 517143450391543818),  # Cafe Regular -> Cafe Visitor
    (538496816845553704, 966298129362202624),  # Fiery Aficionado -> Fiery Adept
    (966298455205097542, 538496816845553704),  # Lantern Voyager -> Fiery Aficionado
    (966298455205097542, 966298334757257216),  # Lantern Voyager -> Fiery Virtuoso
    (966298455205097542, 973065025709277214),  # Lantern Voyager -> Galactic Nobility
    (966298455205097542, 973064417493266452),  # Lantern Voyager -> Universal Royalty
    (973066531082764298, 973066015447613460),  # Prompt Pioneer -> Prompt Participator
    (973066015447613460, 973063466678112286),  # Prompt Participator -> Prompt Peruser
    (983061892002086994, 983060833141674014),  # Stellar Sovereign -> Orbital Overseer
    (983062281699098624, 983060833141674014),  # Neo Overlord -> Orbital Overseer
    (983062659882680401, 983060833141674014),  # Cosmos Conqueror -> Orbital Overseer
    (983062659882680401, 983061892002086994),  # Cosmos Conqueror -> Stellar Sovereign
    (331630636299452446, 978000113786028164),   # Winner -> Compo Finalist
    (409552655623389185, 1169051040662945803),  # Rhythm Master -> Samurai Master
    (409552655623389185, 1169051235278671963),  # Rhythm Master -> Coffee Master
    (409552655623389185, 1169051488916611093),  # Rhythm Master -> Multitasker Master
    (409552655623389185, 1169051621586636891)  # Rhythm Master -> Conduction Master
]

default_role = 831865797545951232

activity = disnake.Game(name="Managing Roles since 1999!")

bot = commands.InteractionBot(intents=intents,
                   allowed_mentions=disnake.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True), activity=activity)
guilds = [770428394918641694, 296802696243970049]


def getLang(inter, section, line):
    language = inter.locale

    languages = {
        'en-US': "translation/lang_en.ini",
        'en-GB': "translation/lang_en.ini",
        'ko': "translation/lang_ko.ini"
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
    await _roles(inter, type='Role', user=inter.target)


@bot.user_command(name='View Role Icons', guild_ids=guilds)
async def view_roleicon_context(inter):
    await _roles(inter, type='Icon', user=inter.target)


@bot.slash_command(description='Allows you to manage your active role, or view the roles of other users.', name='roles',
                   guild_ids=guilds)
async def roles(inter, member: disnake.Member = None, page: int = 1):
    await _roles(inter, type='Role', user=member, page=page)

@bot.slash_command(description='Allows you to manage your active role icon, or view the role icons of other users.',
                   name='icons', guild_ids=guilds)
async def roleicons(inter, member: disnake.Member = None, page: int = 1):
    await _roles(inter, type='Icon', user=member, page=page)


async def _roles(inter, type, returnEmbed=False,
                 user=False, page=1,
                 defer=True):  # Lists a players' roles & role icons and allows them to choose between them.

    if page < 1:
        page = 1

    if not returnEmbed and defer:
        await inter.response.defer(ephemeral=True)

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

    true_items = []

    shortType = ''

    if type == 'Role':
        itemList = roles
        shortType = 'ro'
    else:
        itemList = roleIcons
        shortType = 'ri'
        true_items.append(guild.get_role(default_role))

    for r in itemList:
        try:
            role = guild.get_role(r)
            if role is None:
                database_update('remove', id, role=r)
            else:
                true_items.append(role)
        except Exception as e:
            print(e)

    if page - 1 > (len(true_items)) / 25:
        page = 1

    true_items.sort(reverse=True)
    
    true_items_shortened = true_items[(page - 1) * 25:(page * 25)]

    aList = []

    if not returnEmbed and not user:

        rarities = getLang(inter, 'Translation', 'RARITY_LIST').split(', ')

        Menu = disnake.ui.Select()
        options = []
        for r in true_items_shortened:
            print(r.name, r.id)
            if r.id == default_role:
                name = getLang(inter, 'Translation', 'NO_ICON')
                desc = (getLang(inter, 'Translation', 'NO_ICON_DESC'))
                temp = disnake.SelectOption(label=name, value=f'{shortType}_{r.id}', description=desc)
            else:
                random.seed(f"{r.name}{inter.author.id}")
                quality = random.choice(rarities)
                level = random.randint(0, 100)
                name = r.name
                temp = disnake.SelectOption(label=r.name, value=f'{shortType}_{r.id}',
                                            description=getLang(inter, 'Translation', 'ITEM_RARITY').format(level, quality,
                                                                                                            r.name))
            options.append(temp)
        Menu.options = options
        Menu.custom_id = 'role_select'
        aList.append(Menu)
    else:
        Menu = None

    roleStrList = ''
    PageDown = None
    PageUp = None

    true_length = len(true_items)
    if len(true_items) > 0:
        if true_items[0].id == default_role:
            true_length = len(true_items)-1

    for i in true_items_shortened:
        if i.id != default_role:
            roleStrList = f'{roleStrList}\n{i.mention}'
    if len(true_items) > len(true_items_shortened):
        roleStrList = f'{roleStrList}\n**({((page - 1) * 25) + 1}-{(((page - 1) * 25) + 1) + len(true_items_shortened) - 1})**'

        if true_items[-1] == true_items_shortened[-1] and len(true_items) > 25:
            pageDown = disnake.ui.Button(label='<-', custom_id=f'{shortType}_{page - 1}', style=disnake.ButtonStyle.blurple)
            aList.append(pageDown)
        if true_items[0] == true_items_shortened[0] and len(true_items) > 25:
            pageUp = disnake.ui.Button(label='->', custom_id=f'{shortType}_{page + 1}', style=disnake.ButtonStyle.blurple)
            aList.append(pageUp)

    if true_length != 1:
        type_plural = getLang(inter, section='Translation', line=f'{type.upper()}_PLURAL')
    else:
        type_plural = getLang(inter, section='Translation', line=f'{type.upper()}')

    if id == 9:
        embTitle = getLang(inter, section='Translation', line='ROLES_LIST_BLACKLIST').format(true_length,
                                                                                             type_plural)
    elif user and not isinstance(user, int):
        embTitle = getLang(inter, section='Translation', line='ROLES_LIST_USER').format(user.name, true_length,
                                                                                        type_plural)
    else:
        embTitle = getLang(inter, section='Translation', line='ROLES_LIST_INVOKER').format(true_length, type_plural)

    embed = disnake.Embed(title=embTitle, description=roleStrList, color=0xD8B400)
    if not returnEmbed:
        embed.set_footer(text=getLang(inter, section='Translation', line='ROLE_FOOTER_INFO').format(
            getLang(inter, section='Translation', line=f'{type.upper()}_PLURAL')))
    if len(true_items) != 0 and not returnEmbed and not user:
        embed.set_footer(text=getLang(inter, section='Translation', line='ROLE_FOOTER_DROPDOWN').format(
            getLang(inter, section='Translation', line=f'{type.upper()}')))

    if returnEmbed:
        return embed
    elif len(true_items) > 0 and not user:
        print(aList)
        message = await inter.edit_original_message(components=aList, embed=embed)
    else:
        message = await inter.edit_original_message(embed=embed)


@bot.slash_command(description='Assigns a role to a user.', name='giverole', guild_ids=guilds)
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

# @bot.slash_command(description='Updates your Roles & Assigns any Child Roles', name='update')
# async def update_roles(inter):
#     global masterRoles
#
#     user_roles = get_user_roles(inter.author.id)
#
#     for i in user_roles:
#         for ix in masterRoles:
#             pri, sec = ix
#             if pri == i:
#                 roles_to_add.append(sec)

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
        embeds.append(disnake.Embed(title=getLang(inter, 'Translation', 'LIST_ROLE').format(role.name), description=allUserRoleStr,
                              color=role.color))
    
    allUserIconStr = ''
    if len(userIconList) > 0:
        for au in userIconList:
            allUserIconStr = f'{allUserIconStr}\n{au.name} ({au.mention})'
            if len(allUserIconStr) > 4000:
                allUserIconStr = f'{allUserIconStr}\n{getLang(inter, "Translation", "LIST_ALL_OVERFLOW").format((len(userIconList) - userIconList.index(au)))}'
                break
        embeds.append(disnake.Embed(title=getLang(inter, 'Translation', 'LIST_ICON').format(role.name), description=allUserIconStr,
                                    color=role.color))
    
    if len(embeds) == 0:
        embeds.append(disnake.Embed(title=getLang(inter, 'Translation', 'LIST_ROLE').format(role.name), description=getLang(inter, 'Translation', 'LIST_ROLE_RETURN_NONE'),
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
async def vw_bl(inter, page:int=1):
    user = 9
    await inter.response.defer()
    embed1 = await _roles(inter, 'Role', returnEmbed=True, user=user, page=page)
    embed2 = await _roles(inter, 'Icon', returnEmbed=True, user=user, page=page)
    await inter.edit_original_message(embeds=[embed1, embed2])


@bot.slash_command(name='show', description='Shows off your role inventory publicly!', guild_ids=guilds)
async def showoff(inter):
    await inter.response.defer()
    user = inter.author
    embed1 = await _roles(inter, 'Role', returnEmbed=True, user=user)
    embed2 = await _roles(inter, 'Icon', returnEmbed=True, user=user)
    await inter.edit_original_message(embeds=[embed1, embed2])


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
        await inter.response.send_message(
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
        await _roles(inter, type='Role', page=int(pageNo))
        if custom_id[0:2] == 'ri':
            longvariablethatdoesnothing, pageNo = custom_id.split("_")
            await _roles(inter, type='Icon', page=int(pageNo))


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


#@bot.listen()
async def on_slash_command_error(ctx, error):
    if isinstance(error, disnake.ext.commands.MissingPermissions):
        await ctx.send(getLang(ctx, 'Translation', 'COMMAND_FAILED_BAD_PERMISSIONS'), ephemeral=True)
        return
    elif isinstance(error, disnake.ext.commands.CommandOnCooldown):
        await ctx.send(getLang(ctx, 'Translation', 'COMMAND_FAILED_COOLDOWN'), ephemeral=True)
        return
    await ctx.send(
        getLang(ctx, 'Translation', 'COMMAND_FAILED_UNKNOWN_ERROR').format(error))
    print(error)


bot.run(open('config/token.txt', 'r').read())
