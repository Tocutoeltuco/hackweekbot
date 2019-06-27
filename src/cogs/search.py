import objects.utils as utils
import discord
from discord.ext import commands

utils.set_cog_name("cogs.search")

class SearchCog(commands.Cog, name="Search Cog"):
	"""Searches through roles and users."""
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def list(self, ctx, *role):
		role = ' '.join(role)

		if role=='owner':
			return await ctx.send(ctx.guild.owner.name)

		for r in ctx.guild.roles:
			if r.name==role:
				role = r
				break
		else:
			return await ctx.send("Error: I haven't found the role on this server.")

		members = [m.name for m in ctx.guild.members if role in m.roles]
		await ctx.send("\n".join(members))

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def searchin(self, ctx, *args):
		if len(args)<2:
			return await ctx.send('Invalid syntax for the command.')

		role = ' '.join(args[:-1])
		name = args[-1].lower()

		for r in ctx.guild.roles:
			if r.name==role:
				role = r
				break
		else:
			return await ctx.send("Error: I haven't found the role on this server.")

		members = [m.name for m in ctx.guild.members if role in m.roles and ((m.nick is not None and name in m.nick.lower()) or name in m.name.lower())]
		await ctx.send("\n".join(members))

	@commands.command()
	@utils.command_check()
	@commands.bot_has_permissions(send_messages=True)
	async def discrim(self, ctx):
		discrim = ctx.author.discriminator
		members = [m.display_name for m in ctx.guild.members if m.discriminator==discrim and m!=ctx.author]
		if len(members)==0:
			return await ctx.send("You have an unique discriminator on this server.")
		await ctx.send('\n'.join(members))

def setup(bot):
	bot.add_cog(SearchCog(bot))