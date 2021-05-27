import random


class Card:
    corresp = {'color': {0: 'Trèfle', 1: 'Carreau', 2: 'Pique', 3: 'Coeur'},
               'value': {13: 'As', 1: '2', 2: '3', 3: '4', 4: '5', 5: '6', 6: '7',
                         7: '8', 8: '9', 9: '10', 10: 'Valet', 11: 'Dame', 12: 'Roi'}}

    def __init__(self, card):
        self.id = card
        self.color = self.corresp['color'][self.id[0]]
        self.value = self.corresp['value'][self.id[1]]
        self.points = {'Coeur': 1}.get(self.color, 0) if self.id != (2, 11) else 13

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

    def swap(self, _):
        return [self.play(int(input(f'Carte n°{k + 1} à donner'))) for k in range(3)]

    def my_turn(self, trump, first, heart):
        print(self.name)
        return int(input(my_cards + '\n' + f'(plus petit que {len(self.cards)})' + prompt))

    async def give(self, player, cards):
        cards = [self.cards[c] for c in cards]
        for card in cards:
            player.cards.append(self.cards.pop(self.cards.index(card)))

    def my_cards(self):
        print('Tes cartes sont :\n' + '\n'.join([f'{c + 1}. {card}' for c, card in enumerate(self.cards)]))

    def say(self, string):
        print(string)


class DameDePique:
    r_corresp = {1: 1, 2: 3, 3: 2}

    def __init__(self):
        self.cards = [Card((col, val)) for col in range(4) for val in range(1, 14)]
        self.players = [Player(f'Joueur {k}') for k in range(4)]
        self.heart = False
        self.round = 0
        self.everyone = str()

    async def say(self, string):
        print(string)

    def tell_everyone(self, string, title='Dame de Pique'):
        print(string)

    async def autoplay(self, player, card):
        print(f'{player.name} a joué {card}')

    async def swap(self, messages):
        return [player.swap(msg) for player, msg in zip(self.players, messages)]

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
        await self.tell_everyone('\n'.join([f'{player.name}: {player.points} points' for player in self.players]),
                                 'Points')

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
            await self.tell_everyone('', 'Fin de la partie !')
            classement = [f'{p}. {player.name} ({player.points})' for p, player in
                          enumerate(sorted(self.players, key=lambda p: p.points))]
            await self.tell_everyone('\n'.join(classement), 'Classement ')
            await self.end()

    def sort_players(self, first):
        self.players = [self.players[k % 4] for k in range(first, first + 4)]

    async def swap_cards(self, mod):
        await self.tell_everyone(' '.join([player.name for player in self.players]), 'Échangez vos cartes')
        swaps = [await player.ask_swap() for player in self.players]
        give = await self.swap(swaps)
        for p, player in enumerate(self.players):
            await player.give(self.players[(p + self.r_corresp[mod]) % 4], give[p])
        for player in self.players:
            await player.my_cards()

    async def player_turn(self, player, fold):
        trump = fold[0].color
        play = await player.my_turn(trump, False, self.heart)
        fold.append(player.play(play))
        await player.my_cards()
        return fold

    async def first_player_turn(self):
        play = await self.players[0].my_turn(None, True, self.heart)
        card = self.players[0].play(play)
        return card

    async def play_turn(self, turn):
        await self.tell_everyone('', 'Nouveau pli')
        if turn == 1:
            de_2_trefle = [c for c, card in enumerate(self.players[0].cards) if card.__repr__() == '2 de Trèfle'][0]
            fold = [self.players[0].play(de_2_trefle)]
            await self.autoplay(self.players[0], '2 de Trèfle')
        else:
            await self.say(f'A {self.players[0].name} de jouer')
            fold = [await self.first_player_turn()]
        await self.players[0].my_cards()
        trump = fold[0].color
        for player in self.players[1:]:
            await self.say(f'A {player.name} de jouer')
            fold = await self.player_turn(player, fold)
        winner = fold.index(sorted(filter(lambda c: c.color == trump, fold))[-1])
        self.players[winner].r_points += sum([card.points for card in fold])
        await self.tell_everyone(f'{self.players[winner].name} remporte le pli', 'Fin du pli')
        if 'Coeur' in [card.color for card in fold]:
            self.heart = True
        return winner

    async def last_turn(self):
        fold = [player.play(0) for player in self.players]
        trump = fold[0].color
        for card, player in zip(fold, self.players):
            await player.my_cards()
            await self.autoplay(player, card.__repr__())
        winner = fold.index(sorted(filter(lambda c: c.color == trump, fold))[-1])
        self.players[winner].r_points += sum([card.points for card in fold])
        await self.tell_everyone('', f'{self.players[winner].name} remporte le pli')

    async def end(self):
        pass
