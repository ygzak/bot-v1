import discord
from discord.ext import commands
from json import load, dump
from discord.commands.context import ApplicationContext
from levenshtein import distance

# setup
with open('config.json') as f:
	config = load(f)

with open('script.lua') as f:
	scriptcode = f.read()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# debug
ids = config['debug']['ids'] if config['debug']['enabled'] else None


def has_perms(ctx: ApplicationContext) -> bool:
	print(1, ctx.author.get_role(config["roles"]["perms"]))
	return ctx.author.get_role(config["roles"]["perms"])


def has_whitelist(ctx: ApplicationContext):
	print(2, ctx.author.get_role(config['roles']['whitelist']))
	return ctx.author.get_role(config['roles']['whitelist'])


def guild_only(ctx):
	print(3, ctx.guild is not None)
	return ctx.guild is not None


@bot.event
async def on_ready() -> None:
	print(
		f'Ready! Logged in as {bot.user.name}#{bot.user.discriminator} ({bot.user.id})')


@bot.event
async def on_application_command_error(ctx: ApplicationContext, error):
	if isinstance(error, discord.errors.CheckFailure):
		print(error, type(error))
		await ctx.response.send_message(f'You can\'t use this command!', ephemeral=True)
	else:
		await ctx.response.send_message('An error occured. Please contact the admins.', ephemeral=True)
		print(error)

whitelist = bot.create_group('whitelist')
blacklist = bot.create_group('blacklist')
give = bot.create_group('give')
remove = bot.create_group("remove")
get = bot.create_group('get')
dm = bot.create_group('dm')

# whitelist


@commands.check(has_perms)
@commands.check(guild_only)
@whitelist.command(name='add', guild_ids=ids)
async def wl_add(ctx: ApplicationContext, user: discord.Member):
	if user.get_role(config['roles']['blacklist']):
		return await ctx.response.send_message(f'User is blacklisted', ephemeral=True)

	await user.add_roles(ctx.guild.get_role(config['roles']['whitelist']))
	await ctx.response.send_message(f'Whitelisted {user.mention}.')


@commands.check(has_perms)
@commands.check(guild_only)
@whitelist.command(name='remove', guild_ids=ids)
async def wl_remove(ctx, user: discord.Member):
	await user.remove_roles(ctx.guild.get_role(config['roles']['whitelist']))
	await ctx.response.send_message(f'Removed {user.mention} from the whitelist.')


@commands.check(has_perms)
@commands.check(guild_only)
@whitelist.command(name='info', guild_ids=ids)
async def wl_info(ctx: ApplicationContext):
	users = [user async for user in ctx.guild.fetch_members() if user.get_role(config["roles"]["whitelist"])]

	embed = discord.Embed(
		title=f'{len(users)} whitelisted user{"s" if len(users)>1 else""}', color=0)

	text = ''
	for user in users:
		text += f'● {user.mention}\n'

	embed.add_field(name=f'Users', value=text)

	await ctx.response.send_message(embed=embed)

# blacklist


@commands.check(has_perms)
@commands.check(guild_only)
@blacklist.command(name='add', guild_ids=ids)
async def bl_add(ctx: ApplicationContext, user: discord.Member):
	await user.add_roles(ctx.guild.get_role(config['roles']['blacklist']))
	await ctx.response.send_message(f'Blacklisted {user.mention}.')


@commands.check(has_perms)
@commands.check(guild_only)
@blacklist.command(name='remove', guild_ids=ids)
async def bl_remove(ctx, user: discord.Member):
	await user.remove_roles(ctx.guild.get_role(config['roles']['blacklist']))
	await ctx.response.send_message(f'Removed {user.mention} from the blacklist.')


@commands.check(has_perms)
@commands.check(guild_only)
@blacklist.command(name='info', guild_ids=ids)
async def bl_info(ctx: ApplicationContext):
	users = [user async for user in ctx.guild.fetch_members() if user.get_role(config["roles"]["blacklist"])]

	embed = discord.Embed(
		title=f'{len(users)} blacklisted user{"s" if len(users)>1 else""}', color=0)

	text = ''
	for user in users:
		text += f'● {user.mention}\n'

	embed.add_field(name=f'Users', value=text)

	await ctx.response.send_message(embed=embed)


# give perms


@commands.check(has_perms)
@commands.check(guild_only)
@give.command(name="perms", guild_ids=ids)
async def give_perms(ctx: discord.commands.ApplicationContext, user: discord.Member):
	await user.add_roles(ctx.guild.get_role(config['roles']['perms']))

	await ctx.response.send_message(f'Given permission to {user}.', ephemeral=True)


@commands.check(has_perms)
@commands.check(guild_only)
@remove.command(name="perms", guild_ids=ids)
async def remove_perms(ctx: discord.commands.ApplicationContext, user: discord.Member):
	if user == ctx.author:
		return await ctx.response.send_message("You can't remove the perms from yourself!", ephemeral=True)
	await user.remove_roles(ctx.guild.get_role(config['roles']['perms']))

	await ctx.response.send_message(f'Revoked permission from {user}.', ephemeral=True)


@commands.check(has_perms)
@commands.check(guild_only)
@give.command(name="role", guild_ids=ids)
async def give_role(ctx: discord.commands.ApplicationContext, user: discord.Member, role: str):
	role_name = role

	roles = await ctx.guild.fetch_roles()
	closest = (float("inf"), None)

	for role in roles:
		role: discord.Role

		dist = distance(role_name, role.name)
		if dist < closest[0]:
			closest = (dist, role)

	await user.add_roles(closest[1])

	await ctx.response.send_message(f'Added role {role.name} to {user.mention}', ephemeral=True)


@commands.check(has_perms)
@commands.check(guild_only)
@remove.command(name="role", guild_ids=ids)
async def remove_role(ctx: discord.commands.ApplicationContext, user: discord.Member, role: str):
	role_name = role

	roles = await ctx.guild.fetch_roles()
	closest = (float("inf"), None)

	for role in roles:
		role: discord.Role

		dist = distance(role_name, role.name)
		if dist < closest[0]:
			closest = (dist, role)

	await user.remove_roles(closest[1])

	await ctx.response.send_message(f'Removed role {role.name} from {user.mention}', ephemeral=True)


@commands.check(has_perms)
@bot.slash_command(guild_ids=ids)
async def announce(ctx: discord.commands.ApplicationContext, channel: discord.TextChannel, message: str):
	await channel.send(message)
	await ctx.response.send_message(f'Sent message to {channel.name}!', ephemeral=True)

# get script


@commands.check(has_whitelist)
@commands.check(guild_only)
@get.command(name='script', guild_ids=ids)
async def get_script(ctx: ApplicationContext):
	await ctx.response.send_message(f'```lua\n{scriptcode}```', ephemeral=True)


@commands.check(has_perms)
@commands.check(guild_only)
@dm.command(name='send', guild_ids=ids)
async def dm_send(ctx, user: discord.User, message: str):
	await user.send(message)

	await ctx.response.send_message(f"Sent message to {user.mention}!", ephemeral=True)

bot.run(config['token'])

# TABLE OF CONTENTS

give_perms
give_role

remove_perms
remove_role

# whitelist
wl_add
wl_remove
wl_info

# blacklist
bl_add
bl_remove
bl_info

announce
dm_send


get_script
