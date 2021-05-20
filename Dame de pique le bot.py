import asyncio
import re

import discord
import emoji

import dame_de_pique

bot = discord.Client(intents=discord.Intents.all())

CARDS_REACTIONS = {f'{k} de {couleur}': f"{str(k).lower()}_de_{couleur.lower().replace('è', '')}" for k in
                   list(range(2, 11)) + ['Valet', 'Dame', 'Roi'] for couleur in ['Coeur', 'Pique', 'Trèfle', 'Carreau']}
CARDS_DEF_REACTIONS = {'As de Trèfle': emoji.EMOJI_UNICODE_ENGLISH[':club_suit:'],
                       'As de Pique': emoji.EMOJI_UNICODE_ENGLISH[':spade_suit:'],
                       'As de Carreau': emoji.EMOJI_UNICODE_ENGLISH[':diamond_suit:'],
                       'As de Coeur': emoji.EMOJI_UNICODE_ENGLISH[':heart_suit:']}
REACTIONS_CARDS = {value: key for key, value in {**CARDS_REACTIONS, **CARDS_DEF_REACTIONS}.items()}


def get_emojis(m):
    custom = re.findall(r'<(?P<name>:\w*:)(?P<id>\d*)', m.content)
    unicode = list(map(lambda e: (emoji.UNICODE_EMOJI_ENGLISH[e], ''),
                       filter(lambda l: l in emoji.UNICODE_EMOJI_ENGLISH.keys(), list(m.content))))
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
        hand = '\n'.join([f'{self.emotes[card.__repr__()]} : {card}' for c, card in enumerate(self.cards)])
        self.cards_msg.embeds[0].description = hand
        await self.cards_msg.edit(embed=self.cards_msg.embeds[0])

    async def say(self, string, title='Dame de pique'):
        embed = discord.Embed(title=title, description=string)
        return await self.chan.send(embed=embed)

    async def ask_swap(self):
        embed = discord.Embed(title='Échanger des cartes', description='Choisissez 3 cartes à échanger')
        msg = await self.private_chan.send(embed=embed)
        for card in self.cards:
            if card.__repr__() in self.emotes:
                emote = self.emotes[card.__repr__()]
            else:
                emote = CARDS_DEF_REACTIONS[card.__repr__()]
            await msg.add_reaction(emote)
        return msg

    async def my_turn(self, trump, first, heart):
        cards_list = [card.__repr__() for card in self.cards]

        async def check(m):
            emojis = get_emojis(m)
            if m.author == self.user and len(emojis) == 1 and REACTIONS_CARDS[emojis[0][1:-1]] in cards_list:
                card = self.cards[cards_list.index(emojis[0])]
                if first and (card.color != 'Coeur' or heart):

                    return True
                elif card.color == trump or trump not in [c.color for c in self.cards]:
                    return True
            await m.delete()
            return False

        msg = await bot.wait_for('message', check=await check)
        await msg.add_reaction('✅')
        return cards_list.index(REACTIONS_CARDS[get_emojis(msg)[0][0][1:-1]])


class DameDePique(dame_de_pique.DameDePique):
    def __init__(self, chan, players):
        self.chan = chan
        self.guild = chan.guild
        self.cards = [dame_de_pique.Card((col, val)) for col in range(4) for val in range(1, 14)]
        self.players = [Player(player, self.chan) for player in players]
        self.heart = False
        self.round = 0
        self.everyone = str()
        c_emotes = {name: discord.utils.get(self.guild.emojis, name=card) for name, card in CARDS_REACTIONS.items()}
        self.emotes = {**c_emotes, **CARDS_DEF_REACTIONS}
        for player in self.players:
            player.emotes = self.emotes

    async def setup(self):
        category = await self.guild.create_category('Ma main')
        for player in self.players:
            player.role = await self.guild.create_role(name=player.user.name,
                                                       permissions=self.guild.default_role.permissions)
            await self.guild.get_member(player.user.id).add_roles(player.role)
            overwrites = {
                self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                self.guild.me: discord.PermissionOverwrite(read_messages=True),
                player.role: discord.PermissionOverwrite(read_messages=True)
            }
            player.private_chan = await self.guild.create_text_channel(player.user.name, category=category,
                                                                       overwrites=overwrites)
            embed = discord.Embed(title='Mes cartes', description='')
            player.cards_msg = await player.private_chan.send(embed=embed)

    async def swap(self, messages):
        def check(react, u):
            return react.message in messages and u != bot.user and react.count == 2

        give = [list() for _ in range(4)]
        for index, (player, msg) in enumerate(zip(self.players, messages)):
            swaps = await self.count_reactions(player, await msg.channel.fetch_message(msg.id))
            if len(swaps) >= 3:
                give[index] = swaps[:3]
        while list() in give:
            reaction, _ = await bot.wait_for('reaction_add', check=check)
            msg = reaction.message
            index = messages.index(msg)
            player = self.players[index]
            swaps = await self.count_reactions(player, msg)
            if len(swaps) == 3:
                give[index] = swaps
            elif len(swaps) > 3:
                reaction.remove(player.user)
        for msg in messages:
            await msg.delete()
        return give

    async def count_reactions(self, player, msg):
        cards_list = [card.__repr__() for card in player.cards]
        swaps = list()
        for r in msg.reactions:
            if r.count == 2:
                emote = r.emoji.name if r.custom_emoji else r.emoji
                swaps.append(cards_list.index(REACTIONS_CARDS[emote]))
        if len(swaps) >= 3:
            embed = self.everyone.embeds[0]
            try:
                embed.description = embed.description.replace(player.name + ', ', '').replace(player.name, '')
            except AttributeError:
                pass
            await self.everyone.edit(embed=embed)
        return swaps

    async def say(self, string):
        await self.chan.send(string)

    async def tell_everyone(self, string, title='Dame de pique'):
        embed = discord.Embed(title=title, description=string)
        self.everyone = await self.chan.send(embed=embed)

    async def autoplay(self, player, card):
        emote = self.emotes[card] if card in self.emotes else CARDS_DEF_REACTIONS[card]
        embed = discord.Embed(title=player.user.name, description=emote)
        await self.chan.send(embed=embed)

    async def end(self):
        for player in self.players:
            category = player.private_chan.category
            await player.private_chan.delete()
            await player.role.delete()
        await category.delete()


async def ddp(chan):
    description = 'Ajouter une réaction :spades: pour participer\nAjouter une réaction :x: pour annuler'
    embed = discord.Embed(title='Jouer à la dame de pique', description=description)
    msg = await chan.send(embed=embed)
    await msg.add_reaction('♠')
    await msg.add_reaction('❌')
    s_count, players = 0, list()
    reaction = discord.Reaction(message=None, data={}, emoji=True)

    def check(r, u):
        return r.message == msg and str(r.emoji) in ('❌', '♠') and u != bot.user

    while s_count < 4 and reaction.emoji != '❌':
        reaction, user = await bot.wait_for('reaction_add', check=check)
        if reaction.emoji == '♠':
            players.append(user)
            s_count += 1
        elif reaction.emoji == '❌':
            embed.description = 'Annulation...'
            await msg.edit(embed=embed)
    await msg.clear_reactions()
    if s_count == 4:
        desc = f'Joueuses et joueurs : {", ".join([p.mention for p in players])}'
        embed = discord.Embed(title="C'est parti !", description=desc)
        await chan.send(embed=embed)
        d2p = DameDePique(chan, players)
        await d2p.setup()
        await d2p.play()


async def man(chan):
    with open('files/man.txt', 'r', encoding='utf-8') as f:
        title = f.readline()
        text = f.read()
    embed = discord.Embed(type='rich', title=title, description=text)
    await chan.send(embed=embed)


async def test(chan):
    def check(m):
        return m.channel == chan

    msg = await chan.send('Foo')
    await msg.add_reaction('<:Kappa:673530124259426304>')
    r, _ = await bot.wait_for('reaction_add')
    print(r.message.reactions == msg.reactions)
    for _ in range(50):
        await asyncio.sleep(1)
        print(msg.reactions)


async def regles(chan):
    with open('files/regles.txt', 'r', encoding='utf-8') as f:
        title = f.readline()
        text = f.read()
    embed = discord.Embed(type='rich', title=title, description=text)
    await chan.send(embed=embed)


COMMANDS = {'man': man, 'ddp': ddp, 'test': test, 'règles': regles}


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
