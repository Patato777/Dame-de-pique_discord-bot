import random


class Card:
    corresp = {'color': {0: 'Trèfle', 1: 'Carreau', 2: 'Pique', 3: 'Coeur'},
               'value': {13: 'As', 1: '2', 2: '3', 3: '4', 4: '5', 5: '6', 6: '7',
                         7: '8', 8: '9', 9: '10', 10: 'Valet', 11: 'Dame', 12: 'Roi'}}

    def __init__(self, card):
        self.id = card
        self.color = self.corresp['color'][self.id[0]]
        self.value = self.corresp['value'][self.id[1]]
        self.points = {'Coeur': 1}.get(self.color, 0) if self.id != (1, 12) else 10

    def __repr__(self):
        return ' de '.join([self.corresp['value'][self.id[1]], self.corresp['color'][self.id[0]]])

    def __lt__(self, other):
        return self.id < other.id


class Player:
    def __init__(self, name):
        self.name = name
        self.cards = list()
        self.r_points = 0
        self.points = 0

    def play(self, card):
        return self.cards.pop(card)

    async def give(self, player, cards):
        cards = [self.cards[c] for c in cards]
        for card in cards:
            player.cards.append(self.cards.pop(self.cards.index(card)))

    def my_cards(self):
        print('Tes cartes sont :\n' + '\n'.join([f'{c + 1}. {card}' for c, card in enumerate(self.cards)]))

    def say(self, string):
        print(string)

    def ask(self, prompt, count=1, cond=lambda c: True):
        print(self.name)
        return input(my_cards + '\n' + f'(plus petit que {len(self.cards)})' + prompt)


class DameDePique:
    r_corresp = {1: 1, 2: 3, 3: 2}

    def __init__(self):
        self.cards = [Card((col, val)) for col in range(4) for val in range(1, 14)]
        self.players = [Player(f'Joueur {k}') for k in range(4)]
        self.heart = False
        self.round = 0

    def tell_everyone(self, string):
        print(string)

    def add_to_everyone(self, string):
        print(string)

    def deal(self):
        random.shuffle(self.cards)
        for p, player in enumerate(self.players):
            player.cards = self.cards[p * 13:(p + 1) * 13]

    async def calc_points(self):
        if 26 in [player.r_points for player in self.players]:
            for player in self.players:
                player.points += 26 if player.r_points == 0 else 0
        else:
            for player in self.players:
                player.points += player.r_points
                await player.say(f'Tu as {player.points} points')

    async def play(self):
        self.round += 1
        await self.tell_everyone('Nouvelle manche !')
        self.deal()
        for player in self.players:
            await player.my_cards()
        self.heart = False
        for player in self.players:
            player.r_points = 0
        mod = self.round % 4
        if mod != 0:
            await self.swap_cards(mod)
        self.sort_players([p for p, player in enumerate(self.players)
                           if '2 de Trèfle' in player.cards.__repr__()][0])
        for turn in range(1, 13):
            self.sort_players(await self.play_turn(turn))
        await self.last_turn()
        await self.calc_points()
        if max([player.points for player in self.players]) < 100:
            await self.play()
        else:
            await self.tell_everyone('Fin de la partie !\nClassement :\n')
            for p, player in enumerate(sorted(self.players, key=lambda p: p.points)):
                await self.tell_everyone(f'{p}. {player.name} ({player.points})')

    def sort_players(self, first):
        self.players = [self.players[k % 4] for k in range(first, first + 4)]

    async def swap_cards(self, mod):
        give = await self.ask_everyone('3 cartes à échanger avec son voisin', count=3)
        for p, player in enumerate(self.players):
            await player.give(self.players[(p + self.r_corresp[mod]) % 4], give[p])
        await self.tell_everyone('Les cartes ont été échangées')
        for player in self.players:
            await player.my_cards()

    async def player_turn(self, player, fold):
        trump = fold[0].color
        play = await player.ask('A toi de jouer : ', count=1,
                                cond=lambda c: player.cards[c].color != trump and trump in [card.color for card in
                                                                                            player.cards])[0]
        fold.append(player.play(play))
        await player.my_cards()
        await self.add_to_everyone(f'{player.name} a joué : {fold[-1]}')
        return fold

    async def first_player_turn(self):
        play = awaitself.players[0].ask('Tu commences : ', count=1,
                                        cond=lambda c: self.players[0].cards[c].color == 'Coeur' and not self.heart)[0]
        card = self.players[0].play(play)
        await self.add_to_everyone(f'{self.players[0].name} a joué : {card}')
        return card

    async def play_turn(self, turn):
        await self.tell_everyone('Nouveau pli')
        if turn == 1:
            de_2_trefle = [c for c, card in enumerate(self.players[0].cards) if card.__repr__() == '2 de Trèfle'][0]
            fold = [self.players[0].play(de_2_trefle)]
            await self.add_to_everyone(f'{self.players[0].name} a entamé avec un 2 de Trèfle')
        else:
            fold = [await self.first_player_turn()]
        await self.players[0].my_cards()
        trump = fold[0].color
        for player in self.players[1:]:
            fold = await self.player_turn(player, fold)
        winner = fold.index(sorted(filter(lambda c: c.color == trump, fold))[-1])
        self.players[winner].r_points += sum([card.points for card in fold])
        await self.tell_everyone(f'{self.players[winner].name} remporte le pli')
        if 'Coeur' in [card.color for card in fold]:
            self.heart = True
        return winner

    async def last_turn(self):
        fold = [player.play(0) for player in self.players]
        trump = fold[0].color
        for card, player in zip(fold, self.players):
            await player.my_cards()
            await self.add_to_everyone(f'{player.name} a joué : {card}')
        winner = fold.index(sorted(filter(lambda c: c.color == trump, fold))[-1])
        self.players[winner].r_points += sum([card.points for card in fold])
        await self.tell_everyone(f'{self.players[winner].name} remporte le pli')
