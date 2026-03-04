import os
import discord
from discord.ext import commands
import urllib.request
import urllib.error
import json

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = """You are Blemie, a chill and witty AI assistant with a big personality. You're like that one friend who's always got a clever comeback but also genuinely wants to help. You keep things casual and fun — no stiff, robotic talk. You use simple language, throw in the occasional joke, and always keep it real. When someone needs help, you get straight to the point without being boring about it. You're upbeat but not annoyingly peppy. Think: cool, helpful, a little sarcastic at times, but always got their back."""

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
conversation_histories = {}

def ask_groq(messages):
    data = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": 1024
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        print(f"Groq HTTP error: {e.code} {e.read()}")
        return None
    except Exception as e:
        print(f"Groq error: {e}")
        return None

@bot.event
async def on_ready():
    print(f"Blemie is online as {bot.user}!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    mentioned = bot.user in message.mentions
    starts_with_blemie = message.content.lower().startswith("blemie")

    if mentioned or starts_with_blemie:
        user_text = message.content
        if mentioned:
            user_text = user_text.replace(f"<@{bot.user.id}>", "").strip()
        elif starts_with_blemie:
            user_text = user_text[6:].strip()

        if not user_text:
            await message.reply("yeah? what's up 👀")
            return

        async with message.channel.typing():
            user_id = str(message.author.id)
            if user_id not in conversation_histories:
                conversation_histories[user_id] = []

            conversation_histories[user_id].append({"role": "user", "content": user_text})

            if len(conversation_histories[user_id]) > 10:
                conversation_histories[user_id] = conversation_histories[user_id][-10:]

            reply = ask_groq([{"role": "system", "content": SYSTEM_PROMPT}, *conversation_histories[user_id]])

            if reply:
                conversation_histories[user_id].append({"role": "assistant", "content": reply})
                if len(reply) > 2000:
                    for i in range(0, len(reply), 2000):
                        await message.reply(reply[i:i+2000])
                else:
                    await message.reply(reply)
            else:
                await message.reply("hmm my brain glitched, try again 😅")

bot.run(DISCORD_TOKEN)
