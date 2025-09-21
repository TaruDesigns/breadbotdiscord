import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands
from loguru import logger

from db.service import DBService, User, UserNotFound
from inference.predict import InferenceClient
from settings import SETTINGS
from stats import plots

from .plain_message import FreeMessageHandler


class DiscordBot(commands.Bot):
    def __init__(self, db: DBService, inference: InferenceClient):
        self.db = db
        self.inference = inference
        intents = discord.Intents.default()
        intents.message_content = True
        discord.utils.setup_logging(level=logging.INFO)
        super().__init__(command_prefix="$", intents=intents)
        self.register_handlers()

    def register_handlers(self):
        self.command(name="breadstats")(self.breadstats)
        self.command(name="hello")(self.hello)

    async def on_ready(self):
        logger.info(f"We have logged in as {self.user}")

    async def on_message(self, message: discord.Message):
        logger.debug("Received message!")
        if message.author == self.user:
            return

        user = User(
            author_id=message.author.id,
            author_nickname=message.author.nick if message.author.nick else None,
            author_name=message.author.name,
        )
        self.db.upsert_user_info(user)
        ctx = await self.get_context(message)
        if ctx.valid:
            await self.process_commands(message)
        else:
            await self.on_plain_message(message)

    async def on_plain_message(self, message: discord.Message):
        await message.channel.send(f"You said: {message.content}")
        await self.predict(message)

    @staticmethod
    def parse_message_args(message_content: str) -> list[str]:
        contents = message_content.strip().split(" ")
        return contents[1:]

    async def breadstats(self, ctx: commands.Context, *args):
        """Get your previous stats for the breads you've posted
        Arguments:
        --history : Shows a plot with
        --self : Shows your Best and worst
        --top [n] : Shows the best and worst [n] results for the server"""
        args = self.parse_message_args(ctx.message.content)
        if len(args) < 1:
            await ctx.channel.send(
                content="Not enough arguments", reference=ctx.message
            )
        elif args[0] == "--history":
            await self._breadstats_history(ctx, *args)

        elif args[0] == "--self":
            await self._breadstats_self(ctx, *args)
        elif args[0] == "--top":
            await self._breadstats_top(ctx, *args)
        else:
            await self._breadstats_top(ctx, *args)

    async def _breadstats_self(self, ctx: commands.Context, *args):
        # Return results (top 1) for current user
        try:
            results_min = self.db.get_min_roundness_for_user(ctx.author.id)
            min_roundness_percent = results_min.roundness
        except UserNotFound:
            min_roundness_percent = 0
        try:
            results_max = self.db.get_max_roundness_for_user(ctx.author.id)
            max_roundness_percent = results_max.roundness
        except UserNotFound:
            max_roundness_percent = 0
        reply_content = f"""
                            Hello {ctx.author.name}:
                            Min roundness:  {min_roundness_percent * 100:.2f}% on message: {results_min.replymessage_jump_url},
                            Max roundness {max_roundness_percent * 100:.2f}% on message: {results_max.replymessage_jump_url}
                            """
        await ctx.channel.send(content=reply_content, reference=ctx.message)

    async def _breadstats_history(self, ctx: commands.Context, *args):
        roundness_data = self.db.get_roundness_history(ctx.author.id)
        save_path = (
            SETTINGS.downloads_path / "plots" / f"{ctx.author.id}_roundhistory.png"
        )
        plots.plot_roundness_by_user(roundness_data, save_path)
        discord_file = discord.File(save_path)
        reply_content = "Here's your graph with the roundness history"
        await ctx.channel.send(
            content=reply_content, reference=ctx.message, file=discord_file
        )

    async def _breadstats_top(self, ctx: commands.Context, *args):
        # Return "top X" for the server
        try:
            limit = int(args[2])
            append_to_limit = ""
            if limit > 10:
                limit = 10
                append_to_limit = (
                    f" (You're asking too much, nobody has seen a top {limit} ever)"
                )
        except Exception as e:
            logger.warning(e)
            limit = 3
            append_to_limit = " (You didn't enter a valid number. Shame on you)"
        results_max = self.db.get_max_roundness_leaderboard(limit)
        results_min = self.db.get_min_roundness_leaderboard(limit)
        # Generate message part for top X
        reply_content_max = f"Top {limit}{append_to_limit}:"
        for i, message in enumerate(results_max):
            try:
                user_info = self.db.select_user_info(message.author_id)
            except UserNotFound:
                user_info = User(author_name="unknown", author_id=-1)
            reply_content_max = f"""{reply_content_max}\n #{i + 1}: {user_info.author_name} with {message.roundness * 100:.2f}% on message {message.replymessage_jump_url}"""
        # Generate message part for worst X
        reply_content_min = "Worst 3:"
        for i, message in enumerate(results_min):
            try:
                user_info = self.db.select_user_info(message.author_id)
            except UserNotFound:
                user_info = User(author_name="unknown", author_id=-1)
            reply_content_min = f"""{reply_content_min}\n #{i + 1}: {user_info.author_name} with {message.roundness * 100:.2f}% on message {message.replymessage_jump_url}"""

        reply_content = f"{reply_content_max}\n{reply_content_min}"
        await ctx.channel.send(content=reply_content, reference=ctx.message)

    async def hello(self, ctx: commands.Context, *args):
        """Say hello!"""
        await ctx.channel.send(content="Hello!", reference=ctx.message)

    async def predict(self, message: discord.Message):
        """Main bread inference handler, gets all the relevant data and inserts in DB"""
        # Check Bread Candidate Message

        async def save_attachment(attachment: discord.Attachment) -> Path:
            save_path = SETTINGS.downloads_path / attachment.filename
            await attachment.save(save_path)
            return save_path

        try:
            if FreeMessageHandler.is_bread_candidate(message=message):
                saved_attachments = await asyncio.gather(
                    *[save_attachment(a) for a in message.attachments]
                )
                for file in saved_attachments:
                    await self._send_bread_message(
                        input_file=file,
                        message=message,
                        min_confidence=SETTINGS.bread_detection_confidence,
                    )
            elif FreeMessageHandler.is_areyousure_message(
                message=message, botuser=self.user
            ):
                logger.debug("Are you sure message! Do everything again!")
                # Timeline is:
                # User message with bread pic -> Bot reply -> User reply to bot reply; Invert to get OG message
                ogmessageref = message.reference.resolved.reference
                # For some reason it won't automatically resolve all replies so I have to do it manually
                ogmessage = await self.get_message_by_id(
                    guild_id=ogmessageref.guild_id,
                    channel_id=ogmessageref.channel_id,
                    message_id=ogmessageref.message_id,
                )
                saved_attachments = await asyncio.gather(
                    *[save_attachment(a) for a in message.attachments]
                )
                # TODO: double check that it the og message is a bread message?
                for file in saved_attachments:
                    await self._send_bread_message(
                        input_file=file,
                        message=ogmessage,
                        min_confidence=SETTINGS.override_detection_confidence,
                    )

        except Exception as e:
            logger.error(e)

    async def _send_bread_message(
        self,
        message: discord.Message,
        input_file: Path,
        min_confidence: float,
    ) -> discord.Message:
        """Main "bread analyze" function -> calls the compute function and sends message based on results"""

        # Download and process each attached picture
        async with message.channel.typing():
            # Compute: Get file (or None) and comment to be used
            res = await FreeMessageHandler.compute_bread_message_for_file(
                input_file, self.inference, min_confidence
            )
            out_file, comment, prediction = res
            # Send the image back with the comment
            sent: discord.Message = await message.channel.send(
                file=discord.File(out_file), content=comment, reference=message
            )
        self.db.upsert_message_stats(
            ogmessage_id=message.id,
            roundness=prediction.roundness,
            labels_json=prediction.labels,
        )
        self.db.upsert_message_discordinfo(
            ogmessage_id=message.id,
            replymessage_jump_url=sent.jump_url,
            replymessage_id=sent.id,
            author_id=message.author.id,
            channel_id=message.channel.id,
            guild_id=message.guild.id,
        )
        return sent

    async def get_message_by_id(
        self, guild_id: int, channel_id: int, message_id: int
    ) -> discord.Message:
        guild = self.get_guild(guild_id)
        if guild is None:
            logger.error("Guild not found")
            raise ValueError("Guild not found")

        channel = guild.get_channel(channel_id)
        if channel is None:
            logger.info("Channel not found")
            raise ValueError("Channel not found")

        message = await channel.fetch_message(message_id)
        return message

    async def get_user_by_id(self, user_id: int) -> discord.User:
        user = await self.fetch_user(user_id)
        return user
