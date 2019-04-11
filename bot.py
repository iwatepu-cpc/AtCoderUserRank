import discord
import os
from discord.ext import commands
from discord.utils import get
from AtCoderInfoCache import AtCoderInfoCache

AtCoderUsers = AtCoderInfoCache('cache', 'users.list')
bot = commands.Bot(command_prefix='/', description='サークル雑務コマンド')

__rating_colors__ = [
        (0, (128, 128, 128)),
        (400, (128, 64, 0)),
        (800, (0, 128, 0)),
        (1200, (0, 192, 192)),
        (1600, (0, 0, 255)),
        (2000, (192, 192, 0)),
        (2400, (255, 128, 0)),
        (2800, (255, 0, 0))
]

def mix_colors(records):
    c = (0, 0, 0)
    for record in records:
        _c = (0, 0, 0)
        for rate, color in __rating_colors__:
            if record['rating'] >= rate:
                c = color
            else:
                break
        c = (c[0]+_c[0], c[1]+_c[1], c[2]+_c[2])
    c = (int(c[0]/len(records)), int(c[1]/len(records)), int(c[2]/len(records)))
    html_color = '%02X%02X%02X' % c
    return int(html_color, 16)

def get_rating_zone(records):
    res = {}
    for record in records:
        target = 0
        for rate, _ in __rating_colors__:
            if record['rating'] >= rate:
                target = rate
            else:
                break
        res[record['name']] = target
    return res

def necessary_for_next_rating(records):
    res = {}
    for record in records:
        target = 0
        for rate, _ in reversed(__rating_colors__):
            if record['rating'] < rate:
                target = rate
            else:
                break
        res[record['name']] = target - record['rating']
    return res

@bot.command(pass_context=True)
async def rating(ctx):
    global AtCoderUsers
    records, diffs = AtCoderUsers.get_latest()
    records = list(records.values())
    records.sort(key=lambda r: r['rating'], reverse=True)
    color = mix_colors(records)
    cache = list(AtCoderUsers.cache.values())
    previous_zone = get_rating_zone(cache)
    current_zone = get_rating_zone(records)
    necessary = necessary_for_next_rating(records)
    emoji = get(bot.emojis, name="atcoder")
    embed = discord.Embed(title=f"{emoji}速報", description="AtCoderのレート変動がありました！", color=color)
    for r in records:
        d = diffs[r['name']] if r['name'] in diffs else None
        if d is None:
            t1 = "{0[name]} : {0[rating]}".format(r)
            t2 = "最高レート: **{0[highest_rating]}**  現在の順位: **{0[global_rank]}**  優勝回数: **{0[wins]}**\n".format(r)
            t2 += "昇格まであと**{}**".format(necessary[r['name']])
        else:
            t1 = "{0[name]} : {0[rating]}({1[rating]:+})".format(r, d)
            t1 = t1.replace('+0', 'ー')
            t1 = t1.replace('+', '▲')
            t1 = t1.replace('-', '▼')
            t2 = "最高レート: **{0[highest_rating]}**  現在の順位: **{0[global_rank]}**({1[global_rank]:+})  優勝回数: **{0[wins]}**({1[wins]:+})\n".format(r, d)
            t2 += "昇格まであと**{}**".format(necessary[r['name']])
            t2 = t2.replace('+0', 'ー')
            t2 = t2.replace('+', '▲')
            t2 = t2.replace('-', '▼')
        embed.add_field(name=t1, value=t2, inline=False)
    embed.set_footer(text='© 2019 岩手県立大学 競技プログラミングサークル')
    await ctx.send(embed=embed)
    for username in AtCoderUsers.user_list:
        if username in previous_zone and previous_zone[username] < current_zone[username]:
            await ctx.send("**{}**さんが昇格しました。おめでとう！".format(username))



@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))

def read_token_from_file():
    print('Use token file')
    with open('token') as f:
        return f.read().strip()

token = os.getenv("DISCORD_TOKEN")
if token is None:
    token = read_token_from_file()
else:
    print('Use environment variable token')
bot.run(token)
