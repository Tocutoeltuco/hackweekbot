import asyncio
import objects.utils as utils
import discord
from discord.ext import commands

utils.set_cog_name("cogs.search")

class SearchCog(commands.Cog, name="Search Cog"):
	"""Searches through roles and users."""
	def __init__(self, bot):
		self.bot = bot
		self.emojis = {
			'online': 593950591865323529,
			'offline': 593950591651414057,
			'idle': 593950591869386770,
			'dnd': 593950591634636801
		}

	def get_emoji(self, name):
		return f'<:{name}:{self.emojis[name]}>'

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def list(self, ctx, *role):
		"""{{Find all users having a specified role.}}
		[[Works with the owner's role too.]]
		(([role's name]))
		++.list owner++
		"""
		role = ' '.join(role).lower()

		if role=='owner':
			return await ctx.send(ctx.guild.owner.name)

		for r in ctx.guild.roles:
			if r.name.lower()==role:
				role = r
				break
		else:
			return await ctx.send("Error: I haven't found the role on this server.")

		members = [f"{self.get_emoji(m.status.value)} {m.display_name}" for m in ctx.guild.members if role in m.roles]

		embed = discord.Embed()
		embed.title = f"Members with the role `{role}`:"
		embed.description = "\n".join(members)
		await ctx.send(embed=embed)

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def searchin(self, ctx, *args):
		"""{{Find a user which have a specified role.}}
		[[]]
		(([role] [partial user's name]))
		++.searchin mods patrik++
		"""
		if len(args)<2:
			return await ctx.send('Invalid syntax for the command.')

		role = ' '.join(args[:-1]).lower()
		name = args[-1].lower()

		for r in ctx.guild.roles:
			if r.name.lower()==role:
				role = r
				break
		else:
			return await ctx.send("Error: I haven't found the role on this server.")

		members = []
		for m in ctx.guild.members:
			if role not in m.roles:
				continue
			if m.nick is not None and name in m.nick.lower() or name in m.name.lower():
				members.append(f"{self.get_emoji(m.status.value)} {m.display_name}")

		embed = discord.Embed()
		embed.title = f"Members with the role `{role}`:"
		embed.description = "\n".join(members)
		await ctx.send(embed=embed)

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def discrim(self, ctx):
		"""{{Searches for an user who has the same discriminator as you.}}
		[[I'm looking in all guilds I'm in.]]
		(())
		++.discrim++
		"""
		discrim = ctx.author.discriminator
		members = []
		for guild in ctx.bot.guilds:
			for m in ctx.guild.members:
				if m.discriminator==discrim and m!=ctx.author:
					members.append(f"{self.get_emoji(m.status.value)} {m.name}#{m.discriminator}")
				await asyncio.sleep(10**-5) # can be heavy with lot of guilds

		if len(members)==0:
			return await ctx.send("You have an unique discriminator on this server.")

		embed = discord.Embed()
		embed.title = f"Members with the discriminator `{discrim}`:"
		embed.description = "\n".join(members)
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(SearchCog(bot))