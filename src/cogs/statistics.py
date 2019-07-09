import objects.utils as utils
import discord
import re
from discord.ext import commands

class Statistics(commands.Cog, name="Statistics"):
	def __init__(self, bot):
		self.bot = bot

	async def count(self, guild, field):
		if field == "member":
			return guild.member_count

		elif field == "channel":
			return len(guild.text_channels) + len(guild.voice_channels)

		elif field == "category":
			return len(guild.categories)

		elif field == "role":
			return len(guild.roles) - 1 # not counting @everyone (blank's request, blame him, not me)

		return 0

	async def update_guild(self, guild, update=None):
		fields = {
			"member": None,
			"category": None,
			"channel": None,
			"role": None
		}

		for channel in guild.voice_channels:
			if channel.category is not None:
				continue

			data = re.search(r"^([^ ]+) count: \d+$", channel.name.lower())
			if data is None:
				continue

			field_name = data[1]
			if update is not None:
				if field_name == update:
					fields[update] = channel
					break

			else:
				if field_name in fields:
					fields[field_name] = channel

		if update is None:
			for field, channel in fields.items():
				if channel is None:
					continue

				count = await self.count(guild, field)
				await channel.edit(name=f"{field.capitalize()} count: {count}")
			return

		if fields[update] is not None:
			count = await self.count(guild, update)
			await fields[update].edit(name=f"{update.capitalize()} count: {count}")

	@commands.Cog.listener()
	async def on_ready(self):
		for guild in self.bot.guilds:
			if await utils.cog_check(self.bot, guild, "cogs.statistics"):
				await self.update_guild(guild)

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		if await utils.cog_check(self.bot, guild, "cogs.statistics"):
			await self.update_guild(guild)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if await utils.cog_check(self.bot, member.guild, "cogs.statistics"):
			await self.update_guild(member.guild, update="member")
			await self.update_guild(member.guild, update="bot")

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		if await utils.cog_check(self.bot, member.guild, "cogs.statistics"):
			await self.update_guild(member.guild, update="member")
			await self.update_guild(member.guild, update="bot")

	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		if await utils.cog_check(self.bot, channel.guild, "cogs.statistics"):
			await self.update_guild(channel.guild)

	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		if await utils.cog_check(self.bot, channel.guild, "cogs.statistics"):
			await self.update_guild(channel.guild, update="channel")

	@commands.Cog.listener()
	async def on_guild_role_create(self, role):
		if await utils.cog_check(self.bot, role.guild, "cogs.statistics"):
			await self.update_guild(role.guild, update="role")

	@commands.Cog.listener()
	async def on_guild_role_delete(self, role):
		if await utils.cog_check(self.bot, role.guild, "cogs.statistics"):
			await self.update_guild(role.guild, update="role")

def setup(bot):
	bot.add_cog(Statistics(bot))