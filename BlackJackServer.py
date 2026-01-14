import os
import socket
import threading
import time

from Dealer import Dealer
from Messages import OfferMessage, RequestMessage, ServerPayloadMessage, ClientPayloadMessage, recv_exact_tcp

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

def handle_client(connection, address):
    try :
        try :
            message = recv_exact_tcp(connection, RequestMessage.get_size(), RequestMessage.extractMessage)
            client_name = message.client_name
        except :
            connection.close()
            print(f"client {address} failed to connect due to invalid format")
            return False
        print(f"[{client_name}] client {address} joined the table !!")
        num_of_rounds = message.num_of_rounds
        dealer = Dealer()
        for num in range(num_of_rounds):
            print("-----------------")
            print(f"[{client_name}] started round {num+1}")
            print("-----------------")

            player_sum = 0
            dealer_sum = 0
            dealer.shuffle()

            client_card1 = dealer.deal()
            client_card2 = dealer.deal()
            dealer_card1 = dealer.deal()
            dealer_card2 = dealer.deal()
            print(f"[{client_name}] player's cards : {client_card1} , {client_card2}")
            print(f"[{client_name}] dealer's cards : {dealer_card1}")

            # update scores
            player_sum += dealer.get_points(client_card1) + dealer.get_points(client_card2)
            dealer_sum += dealer.get_points(dealer_card1)

            # if player busted from start , inform player and end round
            game_over = False
            round_status = 0
            if player_sum > 21:
                round_status = 2
                game_over = True
            # sending the first two player's cards and the first dealer's card
            message1 = ServerPayloadMessage(0,client_card1)
            message2 = ServerPayloadMessage(round_status,client_card2)
            message3 = ServerPayloadMessage(0,dealer_card1)
            connection.sendall(message1.get_message())
            connection.sendall(message2.get_message())
            connection.sendall(message3.get_message())

            # loop until client Stands (player's turn)
            while not game_over :
                try :
                    message = recv_exact_tcp(connection, ClientPayloadMessage.get_size(), ClientPayloadMessage.extractMessage)
                except :
                    connection.close()
                    print(f"[{client_name}] client {address} left before game end")
                    return False
                response = message.player_decision
                print(f"[{client_name}] player's turn : {response}")
                if response == "Stand":
                    break

                new_card = dealer.deal()
                print(f"[{client_name}] player's new card : {new_card}")
                player_sum += dealer.get_points(new_card)
                if player_sum > 21:
                    # send message informing
                    lose_message = ServerPayloadMessage(2,new_card)
                    connection.sendall(lose_message.get_message())
                    game_over = True
                    break
                else :
                    not_over_message = ServerPayloadMessage(0, new_card)
                    connection.sendall(not_over_message.get_message())
            # if player busted , continue to next round
            if game_over:
                print(f"[{client_name}] player busted")
                continue

            # if player didn't bust continue to dealer's turn
            # first reveal the hidden card , if dealer busts update player and end round
            dealer_sum += dealer.get_points(dealer_card2)
            round_status = 0
            if dealer_sum > 21:
                round_status = 3
                print(f"[{client_name}] dealer busted")
            if dealer_sum >= 17:
                if dealer_sum < player_sum:
                    print(f"[{client_name}] dealer lost due to lower sum")
                    round_status = 3
                elif player_sum < dealer_sum:
                    print(f"[{client_name}] dealer won due to higher sum")
                    round_status = 2
                else:
                    print(f"[{client_name}] dealer tied")
                    round_status = 1
            message = ServerPayloadMessage(round_status, dealer_card2)
            connection.sendall(message.get_message())

            # start dealing cards till 17/bust (dealer's turn)
            while dealer_sum < 17 :
                # deal and update
                new_card = dealer.deal()
                print(f"[{client_name}] dealer got {new_card}")
                last_card = new_card
                dealer_sum += dealer.get_points(new_card)
                # dealer busted
                if dealer_sum > 21:
                    print(f"[{client_name}] dealer busted")
                    # send message informing
                    win_message = ServerPayloadMessage(3, new_card)
                    connection.sendall(win_message.get_message())
                    break
                # dealer didn't reach 17 , inform user game not over and continue
                if dealer_sum < 17:
                    print(f"[{client_name}] dealer Hits")
                    not_over_message = ServerPayloadMessage(0, new_card)
                    connection.sendall(not_over_message.get_message())
                else :
                    print(f"[{client_name}] dealer Stands")
                    if dealer_sum < player_sum:
                        print(f"[{client_name}] dealer lost due to lower sum")
                        round_status = 3
                    elif player_sum < dealer_sum:
                        print(f"[{client_name}] dealer won due to higher sum")
                        round_status = 2
                    else:
                        print(f"[{client_name}] dealer tied")
                        round_status = 1
                    message = ServerPayloadMessage(round_status, last_card)
                    connection.sendall(message.get_message())
                    break

        print(f"[{client_name}] client {address} has done all his rounds :)")
        connection.close()
        return True
    except :
        print(f"[{client_name}] client {address} left before game end")
        connection.close()
        return False


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("", 0))
TCP_PORT = server.getsockname()[1]
server.listen()

# start broadcasting continuously
broadcast_thread = threading.Thread(target=broadcast, daemon=True)
broadcast_thread.start()

while True:
    connection, address = server.accept()
    handle_client_thread = threading.Thread(target=lambda:handle_client(connection, address), daemon=True)
    handle_client_thread.start()