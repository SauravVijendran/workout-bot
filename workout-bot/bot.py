import discord
from discord.ext import commands, tasks
import sqlite3
import datetime
import matplotlib.pyplot as plt
import io


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Setup DB
conn = sqlite3.connect('workouts.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs (
                user_id TEXT,
                username TEXT,
                date TEXT
            )''')
conn.commit()

# DAILY REMINDER TASK
@tasks.loop(hours=24)
async def daily_reminder():
    channel = bot.get_channel(1383405365080756309)  # replace with your channel ID (integer)
    if channel:
        await channel.send("🌟 Hey fitness fam! Don’t forget to log your workout today using `!log` 💪")

@daily_reminder.before_loop
async def before():
    await bot.wait_until_ready()

# LOG COMMAND
@bot.command()
async def log(ctx):
    today = str(datetime.date.today())
    user_id = str(ctx.author.id)
    username = str(ctx.author.display_name)
    c.execute("INSERT INTO logs (user_id, username, date) VALUES (?, ?, ?)", (user_id, username, today))
    conn.commit()
    await ctx.send(f"✅ {username}, your workout has been logged for today!")

# WEEKLY REPORT
@tasks.loop(hours=168)  # Every 7 days
async def weekly_report():
    channel = bot.get_channel(1383405365080756309)
    if channel:
        week_start = datetime.date.today() - datetime.timedelta(days=7)
        c.execute("SELECT username, COUNT(*) FROM logs WHERE date >= ? GROUP BY username", (str(week_start),))
        results = c.fetchall()
        if results:
            msg = "**📅 Weekly Workout Report:**\n"
            for name, count in results:
                msg += f"• {name}: {count} workouts\n"
            await channel.send(msg)

# MONTHLY LEADERBOARD
@tasks.loop(hours=720)  # Every 30 days
async def monthly_leaderboard():
    channel = bot.get_channel(1383405365080756309)
    if channel:
        month_start = datetime.date.today().replace(day=1)
        c.execute("SELECT username, COUNT(*) FROM logs WHERE date >= ? GROUP BY username", (str(month_start),))
        data = c.fetchall()

        if not data:
            await channel.send("📊 No workouts logged this month.")
            return

        usernames = [x[0] for x in data]
        counts = [x[1] for x in data]

        plt.figure(figsize=(10, 5))
        plt.bar(usernames, counts)
        plt.title('🏆 Monthly Leaderboard')
        plt.xlabel('User')
        plt.ylabel('Workout Count')

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        file = discord.File(buf, filename='leaderboard.png')
        await channel.send("📊 **Monthly Leaderboard**", file=file)
        buf.close()

# START TASKS ON READY
@bot.event
async def on_ready():
    print(f'Bot online as {bot.user}')
    daily_reminder.start()
    weekly_report.start()
    monthly_leaderboard.start()

import os
bot.run(os.getenv("BOT_TOKEN"))
  # replace with your token
