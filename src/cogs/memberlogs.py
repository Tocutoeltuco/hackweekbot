import objects.utils as utils
from discord.ext import commands

utils.set_cog_name("cogs.memberlogs")

class MemberLogs(commands.Cog, name="Member Logs"):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_member_join(self, member):
		config = await self.bot.get_guild_config(member.guild.id)

		if config["welcome_channel"] != "" and config["welcome_message"] != "":
			channel = member.guild.get_channel(int(config["welcome_channel"]))

			if channel is not None:
				try:
					await channel.send(config["welcome_message"].format(
						name=member.name, id=member.id, mention=f"<@{member.id}>", avatar=str(member.avatar_url),
						guild_name=member.guild.name, guild_avatar=str(member.guild.icon_url) if member.guild.icon_url else "no avatar"
					))
				except:
					pass

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		config = await self.bot.get_guild_config(member.guild.id)

		if config["goodbye_channel"] != "" and config["goodbye_message"] != "":
			channel = member.guild.get_channel(int(config["goodbye_channel"]))

			if channel is not None:
				try:
					await channel.send(config["goodbye_message"].format(
						name=member.name, id=member.id, mention=f"<@{member.id}>", avatar=str(member.avatar_url),
						guild_name=member.guild.name, guild_avatar=str(member.guild.icon_url) if member.guild.icon_url else "no avatar"
					))
				except:
					pass

def setup(bot):
	bot.add_cog(MemberLogs(bot))