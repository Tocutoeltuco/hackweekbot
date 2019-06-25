from discord.ext import commands

cog_name = None

def set_cog_name(name):
	global cog_name
	cog_name = name

async def cog_check(bot, guild):
	if cog_name is None:
		raise EnvironmentError("objects.utils.cog_name was never set. Set it with objects.utils.set_cog_name")

	if guild is None:
		return False

	guild_conf = await bot.get_guild_config(guild.id)
	if cog_name in guild_conf["cogs"]:
		return True
	return False

def command_check():
	"""A checker to tell whether the command can execute in this guild or not."""
	async def predicate(ctx):
		return await cog_check(ctx.bot, ctx.guild)

	return commands.check(predicate)

def is_mod_check(in_channel=False):
	"""A checker to tell whether the player is a moderator or not."""
	async def predicate(ctx):
		if (
			ctx.author.guild_permissions.administrator or
			ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.manage_channels or
			ctx.author.guild_permissions.kick_members or ctx.author.guild_permissions.ban_members
		):
			return True
		if in_channel:
			channel_permissions = ctx.author.permissions_in(ctx.channel)
			return channel_permissions.manage_messages or channel_permissions.manage_channels
		return False

	return commands.check(predicate)

def integer(arg):
	try:
		return int(arg)
	except ValueError:
		pass

	try:
		return int(round(float(arg)))
	except ValueError:
		raise commands.BadArgument("Argument is not a number.")

def double(arg):
	try:
		return float(arg)
	except ValueError:
		raise commands.BadArgument("")