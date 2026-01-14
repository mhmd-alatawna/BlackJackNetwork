import threading
import time

from Dealer import Dealer
from Messages import *

max_player_count = 3
time_out_period = 10
total_wins = 0
total_loses = 0
total_ties = 0

class Table :
    def __init__(self):
        self.dealer = Dealer()
        self.players = []
        self.players_sums = {}
        self.dealer_turn = False
        self.round_count = 0
        self.dealer_sum = 0

    def play(self , server):
        global total_wins
        global total_loses
        global total_ties
        try:
            try :
                for i in range(max_player_count) :
                    server.settimeout(time_out_period)
                    connection, address = server.accept()
                    self.players.append((connection,address))
            except :
                if len(self.players) == 0 :
                    print("no players joined :(")
                    return False
            players_messages = {}
            players_to_remove = []
            for connection,address in self.players :
                try:
                    message = recv_exact_tcp(connection, RequestMessage.get_size(), RequestMessage.extractMessage , 30)
                    client_name = message.client_name
                    players_messages[(connection,address)] = message,client_name
                    self.players_sums[(connection,address)] = 0
                except:
                    connection.close()
                    print(f"client {address} failed to connect due to invalid format")
                    players_to_remove.append((connection,address))
            for player in players_to_remove :
                self.players.remove(player)
            for player in self.players :
                message, client_name = players_messages[player]
                connection, address = player
                print(f"[{client_name}] client {address} joined the table !!")

            if len(self.players) == 0 :
                return False

            num_of_rounds = 3
            for num in range(num_of_rounds):
                print("-----------------")
                print(f"round {num + 1} started")
                print("-----------------")
                self.dealer_sum = 0
                self.dealer.shuffle()
                dealer_card1 = self.dealer.deal()
                dealer_card2 = self.dealer.deal()
                players_to_remove = []
                players_who_didnt_bust = []
                print(f"dealer's cards : {dealer_card1}")
                self.dealer_sum += self.dealer.get_points(dealer_card1)

                for player in self.players:
                    self.players_sums[player] = 0

                for player in self.players:
                    message, client_name = players_messages[player]
                    connection, address = player

                    client_card1 = self.dealer.deal()
                    client_card2 = self.dealer.deal()
                    print(f"[{client_name}] player's cards : {client_card1} , {client_card2}")
                    print(f"all used cards : {self.dealer.used_cards}")

                    # update scores
                    self.players_sums[player] += self.dealer.get_points(client_card1) + self.dealer.get_points(client_card2)

                    # if player busted from start , inform player and end round
                    game_over = False
                    round_status = 0
                    if self.players_sums[player] > 21:
                        round_status = 2
                        total_wins += 1
                        game_over = True
                    # sending the first two player's cards and the first dealer's card
                    message1 = ServerPayloadMessage(0, client_card1)
                    message2 = ServerPayloadMessage(round_status, client_card2)
                    message3 = ServerPayloadMessage(0, dealer_card1)
                    connection.sendall(message1.get_message())
                    connection.sendall(message2.get_message())
                    connection.sendall(message3.get_message())

                    # loop until client Stands (player's turn)
                    flag = False
                    while not game_over:
                        try:
                            message = recv_exact_tcp(connection, ClientPayloadMessage.get_size(),
                                                     ClientPayloadMessage.extractMessage , 30)
                        except:
                            connection.close()
                            print(f"[{client_name}] client {address} left before game end")
                            players_to_remove.append(player)
                            flag = True
                            break
                        if flag :
                            break
                        response = message.player_decision
                        print(f"[{client_name}] player's turn : {response}")
                        if response == "Stand":
                            break

                        new_card = self.dealer.deal()
                        print(f"[{client_name}] player's new card : {new_card}")
                        self.players_sums[player] += self.dealer.get_points(new_card)
                        if self.players_sums[player] > 21:
                            # send message informing
                            total_wins += 1
                            lose_message = ServerPayloadMessage(2, new_card)
                            connection.sendall(lose_message.get_message())
                            game_over = True
                            break
                        else:
                            not_over_message = ServerPayloadMessage(0, new_card)
                            connection.sendall(not_over_message.get_message())

                    if flag :
                        continue
                    # if player busted , continue to next round
                    if game_over:
                        print(f"[{client_name}] player busted")
                        continue

                    # if player didn't bust continue to dealer's turn
                    # first reveal the hidden card , if dealer busts update player and end round
                    players_who_didnt_bust.append(player)

                for player in players_to_remove :
                    self.players.remove(player)

                self.dealer_sum += self.dealer.get_points(dealer_card2)
                round_status = 0
                if self.dealer_sum > 21:
                    total_loses += len(players_who_didnt_bust)
                    round_status = 3
                    print(f"dealer busted")
                if self.dealer_sum >= 17:
                    for player in players_who_didnt_bust :
                        message, client_name = players_messages[player]
                        connection, address = player
                        if self.dealer_sum < self.players_sums[player]:
                            print(f"[{client_name}] dealer lost due to lower sum")
                            round_status = 3
                            total_loses += 1
                        elif self.dealer_sum > self.players_sums[player]:
                            print(f"[{client_name}] dealer won due to higher sum")
                            round_status = 2
                            total_wins += 1
                        else:
                            print(f"[{client_name}] dealer tied")
                            round_status = 1
                            total_ties += 1
                for player in players_who_didnt_bust :
                    _, client_name = players_messages[player]
                    connection, address = player

                    message = ServerPayloadMessage(round_status, dealer_card2)
                    connection.sendall(message.get_message())

                # start dealing cards till 17/bust (dealer's turn)
                while self.dealer_sum < 17:
                    # deal and update
                    new_card = self.dealer.deal()
                    print(f"dealer got {new_card}")
                    last_card = new_card
                    self.dealer_sum += self.dealer.get_points(new_card)
                    # dealer busted
                    if self.dealer_sum > 21:
                        print(f"dealer busted")
                        total_loses += len(players_who_didnt_bust)
                        # send message informing
                        for player in players_who_didnt_bust :
                            _, client_name = players_messages[player]
                            connection, address = player

                            win_message = ServerPayloadMessage(3, new_card)
                            connection.sendall(win_message.get_message())
                        break
                    # dealer didn't reach 17 , inform user game not over and continue
                    if self.dealer_sum < 17:
                        print(f"dealer Hits")
                        for player in players_who_didnt_bust:
                            _, client_name = players_messages[player]
                            connection, address = player

                            not_over_message = ServerPayloadMessage(0, new_card)
                            connection.sendall(not_over_message.get_message())
                    else:
                        print(f"dealer Stands")
                        for player in players_who_didnt_bust:
                            message, client_name = players_messages[player]
                            connection, address = player

                            if self.dealer_sum < self.players_sums[player]:
                                print(f"[{client_name}] dealer lost due to lower sum")
                                round_status = 3
                                total_loses += 1
                            elif self.players_sums[player] < self.dealer_sum:
                                print(f"[{client_name}] dealer won due to higher sum")
                                round_status = 2
                                total_wins += 1
                            else:
                                print(f"[{client_name}] dealer tied")
                                round_status = 1
                                total_ties += 1

                            message = ServerPayloadMessage(round_status, last_card)
                            connection.sendall(message.get_message())
                        break
            for player in self.players:
                message, client_name = players_messages[player]
                connection, address = player

                print(f"[{client_name}] client {address} has done all his rounds :)")
                connection.close()
            return True
        except:
            for player in self.players:
                connection, address = player
                print(f"something went wrong !!")
                connection.close()
            return False


BROADCAST_IP = "255.255.255.255"
PORT = 13122
MESSAGE_INTERVAL_SEC = 1
server_name = "greedy dealer 67"

# as we learned in class , each physical connection have its own IP , we need to get the active IP
# so we send a summy message to check which interface (wifi,bluetooth ...) the OS uses .
def get_active_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # some random address
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def broadcast():
    ip = get_active_ip()
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Enable broadcast (turns out OS blocks by default)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print(f"Server started, listening on IP address {ip}")
    while True:
        message = OfferMessage(TCP_PORT, server_name).get_message()
        sock.sendto(message, (BROADCAST_IP, PORT))

        time.sleep(MESSAGE_INTERVAL_SEC)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("", 0))
TCP_PORT = server.getsockname()[1]
server.listen()

# start broadcasting continuously
broadcast_thread = threading.Thread(target=broadcast, daemon=True)
broadcast_thread.start()

while True :
    table = Table()
    table.play(server)
    print(f"wins : {total_wins} , loses : {total_loses} , ties : {total_ties}")


