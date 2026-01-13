import os

from Dealer import Card


def to_int(bytes) :
    return int.from_bytes(bytes, byteorder='big', signed=False)

def to_string(bytes) :
    # remove padding
    clean_bytes = bytes.rstrip(b"\x00")
    # turn to string
    return clean_bytes.decode("utf-8")

# generate cookie without repeating
def next_id_4bytes():
    global cookie_dict
    while True:
        rand_4_bytes = os.urandom(4)
        if cookie_dict.get(rand_4_bytes) is None:
            break
    cookie_dict[rand_4_bytes] = True
    return rand_4_bytes

# takes a string and turns it into 32 bytes
def encode_string(name , size) :
    raw = name.encode("utf-8")
    if len(raw) >= size:
        return raw[:size]
    return raw + b'\x00' * (size - len(raw))

class OfferMessage:
    def __init__(self,TCP_PORT, server_name,cookie_id=0xabcddcba,msg_type=0x2):
        self.cookie_id = cookie_id
        self.msg_type = msg_type
        self.tcp_port = TCP_PORT
        self.server_name = server_name

    def get_message(self):
        cookie_id_bytes = self.cookie_id.to_bytes(4, byteorder='big')
        msg_type_bytes = self.msg_type.to_bytes(1, byteorder="big")
        tcp_bytes = self.tcp_port.to_bytes(2, byteorder="big")
        server_name_bytes = encode_string(self.server_name,32)

        return cookie_id_bytes + msg_type_bytes + tcp_bytes + server_name_bytes

    @staticmethod
    def extractMessage(offer_message):
        cookie_id = to_int(offer_message[:4])
        msg_type = offer_message[4]
        tcp_port = to_int(offer_message[5:7])
        server_name = to_string(offer_message[7:])
        return OfferMessage(tcp_port, server_name,cookie_id, msg_type)
    @staticmethod
    def get_size():
        return 39
    @staticmethod
    def get_type():
        return 0x2

class RequestMessage:
    def __init__(self,num_of_rounds, client_name,cookie_id=0xabcddcba,msg_type=0x3):
        self.cookie_id = cookie_id
        self.msg_type = msg_type
        self.num_of_rounds = num_of_rounds
        self.server_name = client_name

    def get_message(self):
        cookie_id_bytes = self.cookie_id.to_bytes(4, byteorder='big')
        msg_type_bytes = self.msg_type.to_bytes(1, byteorder="big")
        num_of_rounds_bytes = self.num_of_rounds.to_bytes(1, byteorder="big")
        client_name_bytes = encode_string(self.server_name,32)

        return cookie_id_bytes + msg_type_bytes + num_of_rounds_bytes + client_name_bytes

    @staticmethod
    def extractMessage(offer_message):
        cookie_id = to_int(offer_message[:4])
        msg_type = offer_message[4]
        num_of_rounds = offer_message[5]
        client_name = to_string(offer_message[6:])
        return RequestMessage(num_of_rounds, client_name,cookie_id, msg_type)
    @staticmethod
    def get_size():
        return 38
    @staticmethod
    def get_type():
        return 0x3

class ClientPayloadMessage:
    def __init__(self, player_decision, cookie_id=0xabcddcba, msg_type=0x4):
        self.cookie_id = cookie_id
        self.msg_type = msg_type
        self.player_decision = player_decision

    def get_message(self):
        cookie_id_bytes = self.cookie_id.to_bytes(4, byteorder='big')
        msg_type_bytes = self.msg_type.to_bytes(1, byteorder="big")
        player_decision_bytes = encode_string(self.player_decision,5)

        return cookie_id_bytes + msg_type_bytes + player_decision_bytes

    @staticmethod
    def extractMessage(offer_message):
        cookie_id = to_int(offer_message[:4])
        msg_type = offer_message[4]
        player_decision = to_string(offer_message[5:10])

        return ClientPayloadMessage(player_decision,cookie_id,msg_type)

    @staticmethod
    def get_size():
        return 10

    @staticmethod
    def get_type():
        return 0x4

class ServerPayloadMessage:
    def __init__(self, round_status , card , cookie_id=0xabcddcba, msg_type=0x4):
        self.cookie_id = cookie_id
        self.msg_type = msg_type
        self.round_status = round_status
        self.card = card

    def get_message(self):
        cookie_id_bytes = self.cookie_id.to_bytes(4, byteorder='big')
        msg_type_bytes = self.msg_type.to_bytes(1, byteorder="big")
        round_status_bytes = self.round_status.to_bytes(1, byteorder="big")
        card_num_bytes = self.card.num.to_bytes(2, byteorder="big")
        card_suit_bytes = self.card.suit.to_bytes(1, byteorder="big")

        return cookie_id_bytes + msg_type_bytes + round_status_bytes + card_num_bytes + card_suit_bytes

    @staticmethod
    def extractMessage(offer_message):
        cookie_id = to_int(offer_message[:4])
        msg_type = offer_message[4]
        round_status = offer_message[5]
        card_num = to_int(offer_message[6:8])
        card_suit = offer_message[8]
        card = Card(card_num,card_suit)

        return ServerPayloadMessage(round_status,card,cookie_id,msg_type)

    @staticmethod
    def get_size():
        return 9

    @staticmethod
    def get_type():
        return 0x4

