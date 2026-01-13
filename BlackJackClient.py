import socket
import threading
import time
from http.client import responses

from Messages import OfferMessage, RequestMessage, ServerPayloadMessage, ClientPayloadMessage

PORT = 13122


def listen_for_offers():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # allow reusing the same port (in case multiple clients run from the same machine)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(("", PORT))

    print("Client started, listening for offer requests...")

    while True:
        data, address = sock.recvfrom(OfferMessage.get_size())

        message = OfferMessage.extractMessage(data)
        if message.msg_type != OfferMessage.get_type() :
            continue

        print(f"Received offer from {address[0]}")
        # print(f"Cookie ID: {message.cookie_id} , message type: {message.msg_type} , tcp port : {message.tcp_port} , server name: {message.server_name}")
        user_response = input("Would you like to accept the offer ? Y/N")
        if user_response == "Y":
            return message,address[0]


def request_server(server_ip,server_port,num_of_rounds,client_name) :
    # connect to server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    # send a request to the server
    message = RequestMessage(num_of_rounds,client_name)
    client.sendall(message.get_message())

    # get the two player's cards and the dealer's card
    # TCP is reliable so we can assume this order of arrival
    data = client.recv(ServerPayloadMessage.get_size())
    message1 = ServerPayloadMessage.extractMessage(data)
    data = client.recv(ServerPayloadMessage.get_size())
    message2 = ServerPayloadMessage.extractMessage(data)
    data = client.recv(ServerPayloadMessage.get_size())
    message3 = ServerPayloadMessage.extractMessage(data)

    player_card1 = message1.card
    player_card2 = message2.card
    dealer_card1 = message3.card

    print(f"your cards : {player_card1} , {player_card2}")
    print(f"dealer's cards : {dealer_card1}")

    win_count = 0
    tie_count = 0
    lose_count = 0
    while True:
        user_res = input("do you want to Hit or Stand ?")
        x = None
        if user_res in ["Hit" ,"hit" , "Hittt" , "H"] :
            x = "Hittt"
        if user_res in ["Stand" , "S" , "stand"] :
            x = "Stand"

        # send the user response to the server
        message = ClientPayloadMessage(x)
        client.sendall(message.get_message())

        # if user stands then let the dealer keep dealing till he is done
        message = None
        if x == "Stand" :
            while True:
                # get response from server
                data = client.recv(ServerPayloadMessage.get_size())
                message = ServerPayloadMessage.extractMessage(data)
                print(f"dealer's card : {message.card}")
                if message.round_status != 0:
                    break
        else : # otherwise only let the dealer deal one card
            # get response from server
            data = client.recv(ServerPayloadMessage.get_size())
            message = ServerPayloadMessage.extractMessage(data)
            print(f"your card : {message.card}")

        if message.round_status == 0 :
            continue
        elif message.round_status == 1 :
            tie_count += 1
            break
        elif message.round_status == 2 :
            lose_count += 1
            break
        elif message.round_status == 3 :
            win_count += 1
            break
        else :
            pass
    print(f"win/tie/lose : {win_count}/{tie_count}/{lose_count}")
    client.close()

# offers_listener_thread = threading.Thread(target=listen_for_offers, daemon=True)
# offers_listener_thread.start()

client_name = input("Enter your name: ")
offer_details,server_ip = listen_for_offers()
num_of_rounds = int(input("Enter number of rounds you want to play: "))
request_server(server_ip , offer_details.tcp_port,num_of_rounds,client_name)
