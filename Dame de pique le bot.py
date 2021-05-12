import asyncio

import discord

import dame_de_pique

bot = discord.Client()

COUNT = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
COUNT_TRAD = {emoji: e for e, emoji in enumerate(COUNT)}


class Player(dame_de_pique.Player):
    def __init__(self, user, chan):
        self.chan = chan
        self.user = user
        self.name = user.mention
        self.cards = list()
        self.r_points = 0
        self.points = 0

    async def my_cards(self):
        self.cards.sort()
        hand = '\n'.join([f'{c + 1}. {card}' for c, card in enumerate(self.cards)])
        self.cards_msg.embeds[0].description = hand
        await self.cards_msg.edit(embed=self.cards_msg.embeds[0])

    async def say(self, string, title='Dame de pique'):
        embed = discord.Embed(title=title, description=string)
        return await self.chan.send(embed=embed)

    async def dm_say(self, string, title='Dame de pique'):
        embed = discord.Embed(title=title, description=string)
        return await self.user.send(embed=embed)

    async def ask(self, prompt, count=1, cond=lambda c: True, base_msg=None):
        if base_msg is None:
            await self.say(self.user.mention, title=prompt)

        def check(m):
            try:
                ans = set([int(n) - 1 for n in m.content.split(', ')])
            except ValueError:
                return False
            return m.author == self.user and len(ans) == count and all(
                [c in range(len(self.cards)) for c in ans]) and all([cond(self.cards[c]) for c in ans])

        msg = await bot.wait_for('message', check=check)
        content = msg.content
        if base_msg is not None:
            embed = base_msg.embeds[0]
            embed.description = embed.description.replace(self.user.mention, '').replace(', ,', '')
            await base_msg.edit(embed=embed)
        await msg.delete()
        return list(set([int(n) - 1 for n in content.split(', ')]))


class DameDePique(dame_de_pique.DameDePique):
    def __init__(self, chan, players):
        self.chan = chan
        self.cards = [dame_de_pique.Card((col, val)) for col in range(4) for val in range(1, 14)]
        self.players = [Player(player, self.chan) for player in players]
        self.heart = False
        self.round = 0
        self.everyone = None

    async def tell_everyone(self, string):
        embed = discord.Embed(title='Dame de pique', description=string)
        self.everyone = await self.chan.send(embed=embed)

    async def ask_everyone(self, prompt, count=3):
        embed = discord.Embed(title=prompt, description=f'{", ".join([player.user.mention for player in self.players])}')
        msg = await self.chan.send(embed=embed)
        for player in self.players:
            await player.ask(prompt, count=3, base_msg=msg)

    async def add_to_everyone(self, string):
        self.everyone.embeds[0].description += f'\n{string}'
        await self.everyone.edit(embed=self.everyone.embeds[0])


async def ddp(chan):
    description = 'Ajouter une réaction :spades: pour participer\nAjouter une réaction :x: pour annuler'
    embed = discord.Embed(title='Jouer à la dame de pique', description=description)
    msg = await chan.send(embed=embed)
    await msg.add_reaction('♠')
    await msg.add_reaction('❌')
    s_count, players = 0, list()
    reaction = discord.Reaction(message=None, data={}, emoji=True)

    def check(reaction, user):
        return str(reaction.emoji) in ('❌', '♠') and user != bot.user

    timeout = False
    while s_count < 4 and reaction.emoji != '❌' and not timeout:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            timeout = True
            embed.description = 'Temps écoulé, annulation...'
            await msg.edit(embed=embed)
        else:
            if reaction.emoji == '♠':
                players.append(user)
                s_count += 1
            else:
                embed.description = 'Annulation...'
                await msg.edit(embed=embed)
    await msg.clear_reactions()
    if s_count == 4:
        desc = f'Joueuses et joueurs : {", ".join([p.mention for p in players])}'
        embed = discord.Embed(title="C'est parti !", description=desc)
        await chan.send(embed=embed)
    ddp = DameDePique(chan, players)
    for player in ddp.players:
        player.cards_msg = await player.dm_say('', 'Mes cartes')
    await ddp.play()


async def man(chan):
    with open('files/man.txt', 'r', encoding='utf-8') as f:
        title = f.readline()
        text = f.read()
    embed = discord.Embed(type='rich', title=title, description=text)
    await chan.send(embed=embed)


COMMANDS = {'man': man, 'ddp': ddp}


# @bot.event
# async def on_ready():
#    await bot.get_channel(841820253008166912).send('Bonjour ! :wave: :blush:')

@bot.event
async def on_message(msg):
    if bot.user in msg.mentions:
        if 'bonjour' in msg.content.lower() or 'salut' in msg.content.lower():
            await msg.channel.send('Bonjour ! :wave: :blush:')
        else:
            await msg.channel.send('Plaît-il ?')
    elif msg.content.startswith('!') and msg.content[1:] in COMMANDS:
        await COMMANDS[msg.content[1:]](msg.channel)

token = input('Token : ')
bot.run(token)
