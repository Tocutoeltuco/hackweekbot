import objects.utils as utils
import discord
import random
import time
from discord.ext import commands

utils.set_cog_name("cogs.activity")

class ActivityCog(commands.Cog, name="Activity Cog"):
	def __init__(self, bot):
		self.bot = bot
		self.cooldowns = {}
		self.levels = {}
		self.bot.run_later(self.clear_cooldowns(), 6000) # every 10 minutes

	def level_max_exp(self, level):
		return 5 * (level ** 2) + 50 * level + 100

	def exp_to_level(self, exp):
		remaining = exp
		level = 0
		while remaining >= self.level_max_exp(level):
			remaining -= self.level_max_exp(level)
			level += 1
		return level, remaining

	async def clear_cooldowns(self):
		to_delete = []
		current = time.time()
		howmany = 0

		for user, data in self.cooldowns.copy().items():
			howmany += 1
			if howmany == 100:
				await asyncio.sleep(.1)
				howmany = 0
			if data[0] < current:
				to_delete.append(user)
		await asyncio.sleep(.1)

		for user in to_delete:
			del self.cooldowns[user]

		self.bot.run_later(self.clear_cooldowns(), 6000)

	async def reset_week_levels(self):
		print("Resetting the week levels. This may take a while.")

		await self.bot.db.query("UPDATE `user_levels` SET `this_week`=0", fetch=None)
		await self.bot.db.query(f"UPDATE `disk_variables` SET `value`='{time.time()}' WHERE `name`='last_levels_reset'", fetch=None)
		self.bot.run_later(self.reset_week_levels(), 7 * 24 * 60 * 60)

		print("The week levels have been resetted.")

	@commands.Cog.listener()
	async def on_ready(self):
		last_levels_reset = float((await self.bot.db.query("SELECT `value` FROM `disk_variables` WHERE `name`='last_levels_reset'", fetch="one"))["value"])
		self.bot.run_later(self.reset_week_levels(), last_levels_reset + 7 * 24 * 60 * 60, specific=True)

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.author.bot:
			return

		if not isinstance(msg.channel, discord.TextChannel): # private messages lol
			return

		if not await utils.cog_check(self.bot, msg.guild):
			return

		ctx = await self.bot.get_context(msg)
		if ctx.valid: # it is a command
			return

		if (msg.author.id not in self.cooldowns) or self.cooldowns[msg.author.id][0] < time.time():
			self.cooldowns[msg.author.id] = [time.time() + 90, 1]

		else:
			self.cooldowns[msg.author.id][1] += 1

		if self.cooldowns[msg.author.id][1] < 4:
			row = await self.bot.db.query("SELECT `total`, `this_week` FROM `user_levels` WHERE `guild_id`=%s AND `user_id`=%s", str(msg.guild.id), str(msg.author.id), fetch="one")

			howmany = random.randint(5, 20)
			if row is not None:
				level = self.exp_to_level(row["total"])[0]
				row["total"] += howmany
				row["this_week"] += howmany

				if self.exp_to_level(row["total"])[0] != level:
					try:
						await msg.channel.send(f"Congratulations <@{msg.author.id}>! You've reached level {level + 1}.")
					except:
						pass

				await self.bot.db.query("UPDATE `user_levels` SET `total`=%s, `this_week`=%s WHERE `guild_id`=%s AND `user_id`=%s", row["total"], row["this_week"], str(msg.guild.id), str(msg.author.id), fetch=None)

			else:
				await self.bot.db.query("INSERT INTO `user_levels` (`guild_id`, `user_id`, `total`, `this_week`) VALUES (%s, %s, %s, %s)", str(msg.guild.id), str(msg.author.id), howmany, howmany, fetch=None)

	@commands.command()
	@utils.command_check()
	@utils.permission("access_top_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def top(self, ctx, week: bool=False):
		"""{{Shows the experience leaderboard}}
		[[]]
		((<show week leaderboard?>))
		++yes++
		"""
		result = await self.bot.db.query(
			"SELECT `user_id`, `{0}` AS `experience`, `total` FROM `user_levels` WHERE `guild_id`=%s ORDER BY `{0}` DESC LIMIT 20".format("this_week" if week else "total"),
			str(ctx.guild.id), fetch="all"
		)

		if result is not None:
			text = ""
			for index, row in enumerate(result):
				text += f"\n`%02d` <@{row['user_id']}>: **level `{self.exp_to_level(row['total'])[0]}`**, **`{row['experience']}` experience points**" % (index + 1)

			message = await ctx.send(embed=discord.Embed(
				title=f"Top `{len(result)}` experienced users{' of this week' if week else ''}",
				description=text,
				colour=0xffff99
			))
			self.bot.set_answer(ctx.message.id, message)

		else:
			message = await ctx.send(embed=discord.Embed(
				title="Error!",
				description="Sadly, there is no activity information of this server :(",
				colour=0xff6666
			))
			self.bot.set_answer(ctx.message.id, message)

	@commands.command()
	@utils.command_check()
	@utils.permission("access_level_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def level(self, ctx, member: commands.MemberConverter=None):
		"""{{Shows the level of a user}}
		[[]]
		(([name/ping]))
		++yes++
		"""
		member = member or ctx.author
		row = await self.bot.db.query("SELECT `total`, `this_week` FROM `user_levels` WHERE `guild_id`=%s AND `user_id`=%s", str(ctx.guild.id), str(member.id), fetch="one")

		if row is not None:
			level, remaining = self.exp_to_level(row['total'])
			message = await ctx.send(embed=discord.Embed(
				title=f"Activity information of **{member.name}**",
				description=f"""Level: **`{level}`**
Level experience: **`{remaining}`**/**`{self.level_max_exp(level)}`**
Experience earned this week: **`{row['this_week']}`**
Total experience: **`{row['total']}`**""",
				colour=0xffff99
			))
			self.bot.set_answer(ctx.message.id, message)

		else:
			message = await ctx.send(embed=discord.Embed(
				title=f"Activity information of **{member.name}**",
				description=f"""Level: **`0`**
Level experience: **`0`**/**`{self.level_max_exp(0)}`**
Experience earned this week: **`0`**
Total experience: **`0`**""",
				colour=0xffff99
			))
			self.bot.set_answer(ctx.message.id, message)

def setup(bot):
	bot.add_cog(ActivityCog(bot))