import random


class Card:
    def __init__(self,num,suit):
        self.num = num
        self.suit = suit
    def __repr__(self):
        return f"({self.num},{self.suit})"


class Dealer:
    def __init__(self):
        self.card_list = []
        self.shuffle()

    def shuffle(self):
        self.card_list = []
        for num in range(1,14) :
            for suit in range(4) :
                self.card_list.append(Card(num,suit))
        random.shuffle(self.card_list)

    def deal(self):
        return self.card_list.pop()

    def get_points(self, card):
        if card.num == 1 :
            return 11
        elif card.num >= 10 :
            return 10
        else :
            return card.num