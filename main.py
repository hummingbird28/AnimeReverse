import logging

logging.basicConfig(level=logging.INFO)

import requests
from swibots import (
    EmbeddedMedia,
    EmbedInlineField,
    BotContext,
    CommandEvent,
    BotCommand,
    MessageEvent,
    Message,
    Client,
)
from io import BytesIO
from decouple import config

from traceback import format_exc


def time_formatter(milliseconds):
    minutes, seconds = divmod(int(milliseconds / 1000), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)
    tmp = (
        ((str(weeks) + "w:") if weeks else "")
        + ((str(days) + "d:") if days else "")
        + ((str(hours) + "h:") if hours else "")
        + ((str(minutes) + "m:") if minutes else "")
        + ((str(seconds) + "s") if seconds else "")
    )
    if not tmp:
        return "0s"

    if tmp.endswith(":"):
        return tmp[:-1]
    return tmp


BOT_TOKEN = config("BOT_TOKEN", default="")

Bot = Client(token=BOT_TOKEN)
Bot.set_bot_commands(
    [
        BotCommand("start", "Get Start message", True),
        BotCommand("reverse", "Reverse search anime from image!", True),
    ]
)


@Bot.on_command("reverse")
async def reverseImage(ctx: BotContext[CommandEvent]):
    m = ctx.event.message
    reply = await m.get_replied_message()
    if not (reply and reply.is_media):
        return await m.reply_text("Reply to a message!")
    await processMessage(reply)


@Bot.on_command("start")
async def onStart(ctx: BotContext[CommandEvent]):
    m = ctx.event.message
    await m.reply_text(
        f"ℹ️ Hi {m.user.name}, I am Anime Reverse search bot!\nSend me a video or image to get it's origin"
    )


@Bot.on_message()
async def reverseSearch(ctx: BotContext[MessageEvent]):
    m = ctx.event.message
    if not m.personal_chat:
        return
    if not m.is_media:
        return
    await processMessage(m)


async def processMessage(m: Message):
    url = m.media_link
    try:
        data = requests.get(f"https://api.trace.moe/search?url={url}").json()
    except Exception as er:
        print(format_exc())
        return await m.reply_text(f"ERROR: {er}")
    if not data.get("result"):
        return await m.reply_text("No Results found!")
    result = data["result"][0]
    await m.send(
        "*Anime Reverse*",
        embed_message=EmbeddedMedia(
            thumbnail=result["image"],
            title=Bot.user.name,
            description=f"Use @{Bot.user.user_name} to reverse search anime!",
            inline_fields=[
                [
                    EmbedInlineField(
                        "https://img.icons8.com/?size=256&id=1FE2HGszFS4w&format=png",
                        result["filename"],
                        "Anime",
                    ),
                    EmbedInlineField(
                        "https://img.icons8.com/?size=50&id=bjHuxcHTNosO&format=png",
                        round(result["similarity"], 2),
                        "Similarity",
                    ),
                ],
                [
                    EmbedInlineField(
                        "https://img.icons8.com/?size=256&id=JrbE13EfhZWo&format=png",
                        result["episode"],
                        "Episode",
                    ),
                    EmbedInlineField(
                        "",
                        f"{time_formatter(result['from']*1000)} to {time_formatter(result['to']*1000)}",
                        "Frame",
                    ),
                ],
            ],
            header_name="Anime Reverse Search",
            header_icon="https://img.icons8.com/?size=256&id=1FE2HGszFS4w&format=png",
            footer_title=result["filename"],
            footer_icon="https://img.icons8.com/?size=50&id=xZiTPdO57ltQ&format=png",
        ),
    )
    vid = result["video"]
    file = BytesIO(requests.get(vid).content)
    file.name = "video.mp4"
    thumb = BytesIO(requests.get(result["image"]).content)
    thumb.name = "file.png"
    await m.send(
        result["filename"], document=file, description=result["filename"], thumb=thumb
    )


Bot.run()
