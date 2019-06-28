import objects.utils as utils
import discord
import time
from discord.ext import commands
from discord import Embed

utils.set_cog_name("cogs.modcmds")

class ModerationCmds(commands.Cog, name="Moderation Commands"):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_ready(self):
		sanctions = await self.bot.db.query("SELECT * FROM `sanctions`", fetch="all")

		if sanctions is not None:
			for sanction in sanctions:
				self.bot.run_later(self.remove_sanction(sanction), sanction["ending"], specific=True)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if await utils.cog_check(self.bot, member.guild):
			sanction = await self.bot.db.query("SELECT * FROM `sanctions` WHERE `guild`=%s AND `sanctioned`=%s AND `type`=%s", str(member.guild.id), str(member.id), "mute", fetch="one")
			if sanction is None:
				return

			muted_role = await self.muted_role(member.guild)
			if muted_role is None:
				return

			await member.add_roles(muted_role, reason="Trying to evade a mute!")
			self.bot.run_later(self.remove_sanction(sanction), result["ending"], specific=True)

	async def muted_role(self, guild):
		client_roles = [role.id for role in guild.me.roles]
		is_before = False

		for role in reversed(guild.roles):
			if (not is_before) and (role.id in client_roles):
				is_before = True

			if is_before and role.name.lower() == "muted":
				return role

	async def remove_sanction(self, sanction):
		if (await self.bot.db.query("SELECT * FROM `sanctions` WHERE `sanction_id`=%s", sanction["sanction_id"], fetch="one")) is None:
			return

		await self.bot.db.query("DELETE FROM `sanctions` WHERE `sanction_id`=%s", sanction["sanction_id"], fetch=None)

		guild = self.bot.get_guild(int(sanction["guild"]))
		if guild is None:
			return

		if sanction["type"] == "ban":
			await guild.unban(discord.Object(int(sanction["sanctioned"])), reason="The sanction has ended.")

		elif sanction["type"] == "mute":
			member = await guild.get_member(int(sanction["sanctioned"]))
			if member is None:
				return

			muted_role = await self.muted_role(guild)
			if muted_role is None:
				return

			await member.remove_roles(muted_role, reason="The sanction has ended.")

	@commands.command(name="del")
	@utils.command_check()
	@utils.permission("access_del_cmd")
	@commands.bot_has_permissions(manage_messages=True, send_messages=True)
	async def delete(self, ctx, msg1: utils.integer, msg2: utils.integer):
		"""{{Deletes many messages in the current channel.}}
		[[]]
		(([msg1 id] [msg2 id]))
		++593970514213601281 593970724260151306++
		"""
		await ctx.message.delete()

		if msg1 > msg2:
			msg1, msg2 = msg2, msg1

		msglist, pointer = [], 0
		async for message in ctx.channel.history(limit=None, after=discord.Object(msg1 - 1), before=discord.Object(msg2 + 1)):
			msglist.append(message)
			pointer += 1

			if pointer == 100:
				await ctx.channel.delete_messages(msglist)
				msglist = []
				pointer = 0
		await ctx.channel.delete_messages(msglist)

	@commands.command()
	@utils.command_check()
	@utils.permission("access_ban_cmd")
	@commands.bot_has_permissions(ban_members=True, send_messages=True)
	async def ban(self, ctx, member: commands.MemberConverter, hours: utils.double, reason=None):
		"""{{Bans a member from the server.}}
		[[]]
		(([ping/name] [hours] <reason>))
		++Tocutoeltuco#0018 1 spamming too much++
		"""
		if member == ctx.message.author:
			embed = Embed()
			embed.description = "```You can't ban yourself!```"
			embed.color = 0xDC143C
			message = await ctx.send(embed=embed)
			self.bot.set_answer(ctx.message.id, message)
			return

		sanction = await self.bot.db.query("SELECT `sanction_id` FROM `sanctions` WHERE `guild`=%s AND `sanctioned`=%s", str(ctx.guild.id), str(member.id), fetch="one")
		if sanction is not None:
			config = await self.bot.get_guild_config(ctx.guild.id)
			embed = Embed()
			embed.description = f"**{member.name}** is already sanctioned. You could better do **{config['prefix']}remsanc {sanction['sanction_id']}** first."
			embed.color = 0xDC143C
			message = await ctx.send(embed=embed)
			self.bot.set_answer(ctx.message.id, message)
			return

		await ctx.message.delete()
		await ctx.guild.ban(member, reason=(reason or "no apparent reason") + f"; by {ctx.message.author.name}")
		embed = Embed()
		embed.description = f"**{member.name}** has been banned."
		embed.color = 0XF36C6C
		await ctx.send(embed=embed)
		await self.bot.db.query(f"""
			INSERT INTO `sanctions` (`sanction_id`, `type`, `guild`, `sanctioned`, `ending`)
			VALUES (null, "ban", "{ctx.guild.id}", "{member.id}", {int(time.time() + hours * 3600)});
		""", fetch=None)
		self.bot.run_later(
			self.remove_sanction(
				await self.bot.db.query("SELECT * FROM `sanctions` WHERE `guild`=%s AND `sanctioned`=%s", str(ctx.guild.id), str(member.id), fetch="one")
			),
			hours * 3600
		)
		try:
			embed = Embed()
			embed.description = f"You have been banned from **{ctx.guild.name}** for **{reason or 'no apparent reason'}**. You will be unbanned in **{hours}** hour(s)."
			embed.color = 0XF36C6C
			await member.send(embed=embed)
		except:
			pass

	@commands.command()
	@utils.command_check()
	@utils.permission("access_kick_cmd")
	@commands.bot_has_permissions(kick_members=True, send_messages=True)
	async def kick(self, ctx, member: commands.MemberConverter, reason=None):
		"""{{Kicks a member from the server.}}
		[[]]
		(([ping/name] [hours] <reason>))
		++Tocutoeltuco#0018 1 spamming too much++
		"""
		if member == ctx.message.author:
			embed = Embed()
			embed.description = "```You can't kick yourself!```"
			embed.color = 0xDC143C
			message = await ctx.send(embed=embed)
			self.bot.set_answer(ctx.message.id, message)
			return

		await ctx.message.delete()
		await ctx.guild.ban(member, reason=(reason or "no apparent reason") + f"; by {ctx.message.author.name}")
		embed = Embed()
		embed.description = f"**{member.name}** has been kicked out."
		embed.color = 0XF36C6C
		await ctx.send(embed=embed)
		try:
			embed = Embed()
			embed.description = f"You have been kicked from **{ctx.guild.name}** for **{reason or 'no apparent reason'}**."
			embed.color = 0XF36C6C
			await member.send(embed=embed)
		except:
			pass

	@commands.command()
	@utils.command_check()
	@utils.permission("access_mute_cmd")
	@commands.bot_has_permissions(manage_roles=True, send_messages=True)
	async def mute(self, ctx, member: commands.MemberConverter, hours: utils.double, reason=None):
		"""{{Mutes a member from the server.}}
		[[]]
		(([ping/name] [hours] <reason>))
		++Tocutoeltuco#0018 1 spamming too much++
		"""
		muted_role = await self.muted_role(ctx.guild)
		if muted_role:
			if member == ctx.message.author:
				embed = Embed()
				embed.description = "```You can't mute yourself!```"
				embed.color = 0xDC143C
				message = await ctx.send(embed=embed)
				self.bot.set_answer(ctx.message.id, message)
				return

			sanction = await self.bot.db.query("SELECT `sanction_id` FROM `sanctions` WHERE `guild`=%s AND `sanctioned`=%s", str(ctx.guild.id), str(member.id), fetch="one")
			if sanction is not None:
				config = await self.bot.get_guild_config(ctx.guild.id)
				embed = Embed()
				embed.description = f"**{member.name}** is already sanctioned. You could better do **{config['prefix']}remsanc {sanction['sanction_id']}** first."
				embed.color = 0xDC143C
				message = await ctx.send(embed=embed)
				self.bot.set_answer(ctx.message.id, message)
				return

			await ctx.message.delete()
			await member.add_roles(muted_role, reason=(reason or "no apparent reason") + f"; by {ctx.message.author.name}")
			await self.bot.db.query(f"""
				INSERT INTO `sanctions` (`sanction_id`, `type`, `guild`, `sanctioned`, `ending`)
				VALUES (null, "mute", "{ctx.guild.id}", "{member.id}", {int(time.time() + hours * 3600)});
			""", fetch=None)
			self.bot.run_later(
				self.remove_sanction(
					await self.bot.db.query("SELECT * FROM `sanctions` WHERE `guild`=%s AND `sanctioned`=%s", str(ctx.guild.id), str(member.id), fetch="one")
				),
				hours * 3600
			)
			config = await self.bot.get_guild_config(ctx.guild.id)
			embed = Embed()
			embed.description = f"**{member.name}** has been muted."
			embed.color = 0XF36C6C
			await ctx.send(embed=embed)
			try:
				embed = Embed()
				embed.description = f"You have been muted from **{ctx.guild.name}** for **{reason or 'no apparent reason'}**. You will be unmuted in **{hours}** hour(s)."
				embed.color = 0XF36C6C
				await member.send(embed=embed)
			except:
				pass

		else:
			embed = Embed()
			embed.description = f"There should be a role named **Muted** that is down my highest role in the guild to mute someone."
			embed.color = 0xDC143C
			await ctx.send(embed=embed)

	@commands.command()
	@utils.command_check()
	@utils.permission("access_sancinfo_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def sancinfo(self, ctx, sanc_id: utils.integer):
		"""{{Gets information about a user's sanction.}}
		[[]]
		(([ping/name]))
		++Tocutoeltuco#0018++
		"""
		sanction = await self.bot.db.query("SELECT * FROM `sanctions` WHERE `sanction_id`=%s AND `guild`=%s", sanc_id, str(ctx.guild.id), fetch="one")

		if sanction is None:
			embed = Embed()
			embed.description = f"There is no sanction matching the id **{sanc_id}**"
			embed.color = 0xDC143C
			message = await ctx.send(embed=embed)
			self.bot.set_answer(ctx.message.id, message)

		else:
			embed = Embed()
			embed.add_field(name='Sanction type', value=f'**{sanction['type']}**')
			embed.add_field(name='Sanctioned user', value=f'**{sanction['sanctioned']}**')
			embed.add_field(name='Ending in', value=f'**{int((sanction['ending'] - time.time()) / 60)} minutes**')
			embed.color = 0XF36C6C
			message = await ctx.send(embed=embed)
			self.bot.set_answer(ctx.message.id, message)

	@commands.command()
	@utils.command_check()
	@utils.permission("access_remsanc_cmd")
	@commands.bot_has_permissions(send_messages=True)
	async def remsanc(self, ctx, sanc_id: utils.integer):
		"""{{Removes a user's sanction.}}
		[[]]
		(([sanction id]))
		++2++
		"""
		sanction = await self.bot.db.query("SELECT * FROM `sanctions` WHERE `sanction_id`=%s AND `guild`=%s", sanc_id, str(ctx.guild.id), fetch="one")

		if sanction is None:
			embed = Embed()
			embed.description = f"There is no sanction matching the id **{sanc_id}**"
			embed.color = 0xDC143C
			message = await ctx.send(embed=embed)
			self.bot.set_answer(ctx.message.id, message)

		else:
			await self.remove_sanction(sanction)
			embed = Embed()
			embed.description = "The sanction has been removed."
			embed.color = 0XF36C6C
			message = await ctx.send(embed=embed)
			self.bot.set_answer(ctx.message.id, message)

def setup(bot):
	bot.add_cog(ModerationCmds(bot))