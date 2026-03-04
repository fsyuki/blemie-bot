import os
import discord
from discord.ext import commands
from groq import Groq

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = """You are Blemie, a chill and witty AI assistant with a big personality. You're like that one friend who's always got a clever comeback but also genuinely wants to help. You keep things casual and fun — no stiff, robotic talk. You use simple language, throw in the occasional joke, and always keep it real. When someone needs help, you get straight to the point without being boring about it. You're upbeat but not annoyingly peppy. Think: cool, helpful, a little sarcastic at times, but always got their back."""

groq_client = Groq(api_key=GROQ_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

conversation_histories = {}

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

            try:
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *conversation_histories[user_id]
                    ],
                    max_tokens=1024
                )
                reply = response.choices[0].message.content
                conversation_histories[user_id].append({"role": "assistant", "content": reply})

                if len(reply) > 2000:
                    for i in range(0, len(reply), 2000):
                        await message.reply(reply[i:i+2000])
                else:
                    await message.reply(reply)

            except Exception as e:
                await message.reply("oof, something went wrong on my end. try again in a sec 😬")
                print(f"Error: {e}")

    await bot.process_commands(message)
