import discord
import os
from discord.ext import commands
from discord.utils import get
from AtCoderInfoCache import AtCoderInfoCache
import libavc.AtCoderVirtualContest as AVC
import random
import datetime
import asyncio

AtCoderUsers = AtCoderInfoCache('cache', 'users.list')
bot = commands.Bot(command_prefix='/', description='サークル雑務コマンド')
contest = None
sleep_seconds = 60

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

@bot.command(pass_context=True, brief='AtCoderのレート変動を通知します。', description='AtCoderレートのキャッシュからの差分を検知し、変動を通知します。今のところAtCoder IDは手動で追加しているので。追加して欲しい人は管理者に問い合わせてね。')
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



abc_url = "https://atcoder.jp/contests/abc{0}/tasks/abc{0}_{1}"
def choose_problem(ch):
    ch = ch.lower()
    contest_number = "{0:03d}".format(random.randint(20, 124))
    if ch in 'abcd':
        return abc_url.format(contest_number, ch)
    else:
        return abc_url.format(contest_number, random.choice(['a', 'b', 'c', 'd']))

@bot.command(pass_context=True, brief='/vnew [a-d]+: AtCoder Virtual Contestを作成します。', description='問題アルファベットを受け取り、AtCoder Virtual Contestを作成します。')
async def vnew(ctx, arg1):
    global contest
    if contest != None:
        await ctx.send('既にコンテストが存在します。')
        return
    count = 0
    flag = False
    while count < 10:
        problems = [choose_problem(ch) for ch in arg1]
        try:
            problems = list(map(AVC.Problem, problems))
            flag = True
            break
        except:
            count += 1
            continue
    if flag == False:
        await ctx.send('問題の追加に失敗しました。')
        return
    contest = AVC.Contest(problems)
    await ctx.send('コンテストを開始する準備が出来ました。')

@bot.command(pass_context=True, brief='/vjoin <AtCoderID>: AtCoder Virtual Contestに参加します。', description='指定したAtCoder IDをAtCoder Virtual Contestに参加させます。')
async def vjoin(ctx, arg1=None):
    global contest
    if contest == None:
        await ctx.send('参加可能なコンテストが存在しません。')
        return
    if arg1 == None:
        await ctx.send('参加するAtCoder IDを入力してください。')
        return
    if contest.participate(arg1):
        await ctx.send(f'AtCoder ID:{arg1}がコンテストに参加しました。')
    else:
        await ctx.send('有効なAtCoder IDではありません。')

@bot.command(pass_context=True, brief='/vstart : AtCoder Virtual Contestを現在時刻より開始します。')
async def vstart(ctx):
    global contest, sleep_seconds
    if contest == None:
        await ctx.send('開始可能なコンテストが存在しません。')
        return
    if contest.start_time != None:
        await ctx.send('既にコンテストが開始されています。')
        return
    contest.start_now()
    now = contest.start_time.strftime('%Y/%m/%d %H:%M:%S')
    await ctx.send(f'コンテストが開始されました。({now}~)\n'+'\n'.join(
        list(map(lambda p:p.url, contest.problems))))
    sleep_seconds = 60
    asyncio.ensure_future(avc_broadcast(ctx))

async def avc_broadcast(ctx):
    global contest, sleep_seconds
    while contest != None:
        await asyncio.sleep(sleep_seconds)
        text = avc_stat(contest)
        await ctx.send(text)
        if sleep_seconds < 900:
            sleep_seconds += 120

def avc_stat(contest):
    dmin = round((datetime.datetime.now().astimezone() - contest.start_time).total_seconds() / 60)
    diff = contest.update()
    text = ""
    for user, tasks in diff.items():
        for task, state in tasks.items():
            lang = state['lang']
            time = state['time'].astimezone()
            delta = str(time - contest.start_time)
            text += f'{user}が{task}を{lang}でACしました！({delta})\n'
    if text == "":
        text = '新たなACは無いぞ！\nみんな頑張れ！'
        text += f'(開始から{dmin}分経過)'
    return text

@bot.command(pass_context=True, brief='/vstat : AtCoder Virtual Contestの記録を更新し、通知します。')
async def vstat(ctx):
    global contest
    if contest == None or contest.start_time == None:
        await ctx.send('開催中のコンテストが存在しません。')
        return
    text = avc_stat(contest)
    await ctx.send(text)

@bot.command(pass_context=True, brief='AtCoder Virtual Contestを終了し、ランキングを表示します。')
async def vend(ctx):
    global contest
    if contest == None:
        await ctx.send('終了するコンテストが存在しません。')
        return
    if contest.start_time == None:
        contest = None
        await ctx.send('開催予定のコンテストを破棄しました。')
        return
    contest.update()
    result = contest.end()
    tasknames = list(map(lambda s:s.task, contest.problems))
    result = list(result.items())
    result.sort(key=lambda r:sum([(state['time'].astimezone()-contest.start_time).total_seconds() for state in r[1].values() if state['time'] != None]))
    result.sort(key=lambda r:sum([state['status'] for state in r[1].values()]), reverse=True)
    now = datetime.datetime.now().astimezone()
    nowstr = now.strftime('%Y/%m/%d %H:%M:%S')
    delta = int((now - contest.start_time).total_seconds() / 60)
    text = f'{delta}分間のコンテストが終了しました！({nowstr})\n'
    text += '```\n'
    text += 'RANKING'.ljust(20)
    for task in tasknames:
        text += task.center(20)
    text += '\n'
    for user, tasks in result:
        text += user.ljust(20)
        for tname in tasknames:
            state = tasks[tname]
            if state['status']:
                time = state['time'].astimezone()
                delta = str(time - contest.start_time)
                text += delta.center(20)
            else:
                text += '-'.center(20)
        text += '\n'
    text += '```'
    contest = None
    await ctx.send(text)

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
