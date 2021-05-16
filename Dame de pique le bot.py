import asyncio
import re

import discord
import emoji

import dame_de_pique

bot = discord.Client()


def get_emojis(m):
    custom = re.findall(r'<(?P<name>:\w*:)(?P<id>\d*)', m.content)
    unicode = list(map(lambda e: (emoji.UNICODE_EMOJI_ENGLISH[e], ''),
                       filter(lambda l: l in emoji.UNICODE_EMOJI_ENGLISH.keys(), m.content)))
    return custom + unicode


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

    async def my_turn(self, trump, first, heart):
        cards_list = [card.__repr__() for card in self.cards]

        def check(m):
            emojis = get_emojis(m)
            if m.author == self.user and len(emojis) == 1 and CARDS[emojis[0][1:-1]] in cards_list:
                card = self.cards[cards_list.index(emojis[0])]
                if first and (card.color != 'Coeur' or heart):
                    return True
                elif card.color == trump or trump not in [c.color for c in self.cards]:
                    return True
            m.delete()
            return False

        msg = await bot.wait_for('message', check=check)
        await msg.add_reaction('✅')
        return self.cards[cards_list.index(get_emojis(msg)[0])]


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


async def repeat(chan):
    def check(m):
        return m.channel == chan

    msg = await bot.wait_for('message', check=check)
    print(get_emojis(msg))


COMMANDS = {'man': man, 'ddp': ddp, 'repeat': repeat}


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
