import socket
import threading
import time
from http.client import responses

from Messages import OfferMessage, RequestMessage, ServerPayloadMessage, ClientPayloadMessage, recv_exact_tcp

PORT = 13122

def listen_for_offers(offers_max_count):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # allow reusing the same port (in case multiple clients run from the same machine)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(("", PORT))

    print("Client started, listening for offer requests...")
    offers_dict = {}
    rejected_count = offers_max_count * 2
    while offers_max_count > 0 and rejected_count > 0:
        try :
            # dont get stuck on a sender
            sock.settimeout(0.5)
            data, address = sock.recvfrom(OfferMessage.get_size())
            message = OfferMessage.extractMessage(data)
        except :
            rejected_count -= 1
            continue

        print(f"Received offer from {address[0]} | {message.server_name}")
        offers_dict[str(address[0])] = (message,address[0])
        offers_max_count -= 1
    sock.close()
    return offers_dict


def request_server(server_ip,server_port,num_of_rounds,client_name) :
    # connect to server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    # send a request to the server
    message = RequestMessage(num_of_rounds,client_name)
    client.sendall(message.get_message())

    win_count = 0
    tie_count = 0
    lose_count = 0
    cards_counter = {}
    for i in range(num_of_rounds):
        print("----------------------------")
        print(f"round {i+1} is starting")
        print("----------------------------")

        # get the two player's cards and the dealer's card
        # TCP is reliable so we can assume this order of arrival
        try:
            message1 = recv_exact_tcp(client, ServerPayloadMessage.get_size(), ServerPayloadMessage.extractMessage)
            message2 = recv_exact_tcp(client, ServerPayloadMessage.get_size(), ServerPayloadMessage.extractMessage)
            message3 = recv_exact_tcp(client, ServerPayloadMessage.get_size(), ServerPayloadMessage.extractMessage)
        except :
            client.close()
            return False

        player_card1 = message1.card
        player_card2 = message2.card
        dealer_card1 = message3.card

        cards_counter[player_card1.num] = cards_counter.get(player_card1.num , 0) + 1
        cards_counter[player_card2.num] = cards_counter.get(player_card1.num , 0) + 1
        cards_counter[dealer_card1.num] = cards_counter.get(player_card1.num , 0) + 1


        print(f"your cards : {player_card1} , {player_card2}")
        print(f"dealer's cards : {dealer_card1}")

        while True:
            # loop until user enters stand/hit
            while True :
                user_res = input("do you want to Hit or Stand : ")
                x = None
                if user_res in ["Hit" ,"hit" , "Hittt" , "H"] :
                    x = "Hittt"
                    break
                if user_res in ["Stand" , "S" , "stand"] :
                    x = "Stand"
                    break

            # send the user response to the server
            message = ClientPayloadMessage(x)
            client.sendall(message.get_message())

            # if user stands then let the dealer keep dealing till he is done
            message = None
            if x == "Stand" :
                while True:
                    # get response from server
                    try :
                        message = recv_exact_tcp(client, ServerPayloadMessage.get_size(), ServerPayloadMessage.extractMessage)
                    except :
                        client.close()
                        return False
                    print(f"dealer's card : {message.card}")
                    if message.round_status != 0:
                        break
            else : # otherwise only let the dealer deal one card
                # get response from server
                try:
                    message = recv_exact_tcp(client, ServerPayloadMessage.get_size(), ServerPayloadMessage.extractMessage)
                except:
                    client.close()
                    return False
                print(f"your card : {message.card}")
                cards_counter[message.card.num] = cards_counter.get(player_card1.num , 0) + 1

            if message.round_status == 0 :
                continue
            elif message.round_status == 1 :
                tie_count += 1
                print("you and dealer got a tie")
                break
            elif message.round_status == 2 :
                lose_count += 1
                print("you lost")
                break
            elif message.round_status == 3 :
                win_count += 1
                print("you won !!!!")
                break
            else :
                pass
    print(f"win/tie/lose : {win_count}/{tie_count}/{lose_count}")
    for num,count in cards_counter.items():
        print(f"number : {num} , appears : {count}")
    client.close()
    return True

# offers_listener_thread = threading.Thread(target=listen_for_offers, daemon=True)
# offers_listener_thread.start()

client_name = input("Enter your name: ")
max_offers_count = int(input("Enter max number of offers: "))
while True:
    try :
        # this loop allows the user to keep looking for offers until he is satisfied
        # when exiting the loop it is promised that the user accepted a valid offer
        user_response = "C"
        while user_response == "C" :
            offers_dict = listen_for_offers(max_offers_count)
            user_response = str(input("Which address you want to connect to , enter C to continue looking : "))

            while user_response != "C" and offers_dict.get(user_response) is None :
                print("you entered an invalid offer address")
                user_response = str(input("Which address you want to connect to , enter C to continue looking : "))


        offer_details,server_ip = offers_dict[user_response]
        num_of_rounds = int(input("Enter number of rounds you want to play: "))
        if not request_server(server_ip , offer_details.tcp_port,num_of_rounds,client_name) :
            print("server didn't respond or something went wrong")
    except :
        print("server didn't respond or something went wrong")
