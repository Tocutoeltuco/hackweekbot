import objects.utils as utils
import discord
import random
import time
from discord.ext import commands

utils.set_cog_name("cogs.messagesedit")

class MessagesEditCog(commands.Cog, name="Messages Cog"):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_raw_message_edit(self, payload):
		answer = await self.bot.get_answer(payload.message_id)

		if (answer is not None) and (payload.cached_message is None):
			message = await answer.channel.fetch_message(payload.message_id)

		elif getattr(payload, "cached_message", None) is not None:
			message = payload.cached_message

		elif "guild_id" in payload.data and payload.data["guild_id"] is not None:
			guild = self.bot.get_guild(int(payload.data["guild_id"]))

			if guild is not None:
				channel = guild.get_channel(int(payload.data["channel_id"]))
				message = await channel.fetch_message(int(payload.data["message_id"]))

			else:
				return

		else:
			return

		if answer is not None:
			await answer.delete()
		await self.bot.process_commands(message)

	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		answer = await self.bot.get_answer(payload.message_id)

		if answer is not None:
			await answer.delete()

	@commands.Cog.listener()
	async def on_raw_bulk_message_delete(self, payload):
		answers = []

		for message_id in payload.message_ids:
			answer = await self.bot.get_answer(message_id)

			if answer is not None:
				answers.append(answer)

		if len(answers) > 0:
			await answers[0].channel.delete_messages(answers)

def setup(bot):
	bot.add_cog(MessagesEditCog(bot))