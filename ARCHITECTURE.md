# System Architecture – Multiplayer Blackjack

## 1. Architecture Overview
The system follows a **client–server architecture** with two server execution models.

- UDP is used for server discovery
- TCP is used for all gameplay communication
- The server fully controls the game logic
- Clients act as decision senders only

---

## 2. Network Model

### UDP Discovery
- Broadcast address: 255.255.255.255
- Port: 13122
- Broadcast interval: 1 second

Servers broadcast:
- TCP port
- Server name
- Protocol cookie

---

### TCP Gameplay
- Reliable, ordered communication
- Fixed-size binary messages
- Blocking reads using `recv_exact_tcp`

---

## 3. Message Protocol

### OfferMessage
| Field | Size |
|------|------|
| Cookie ID | 4 bytes |
| Message Type | 1 byte |
| TCP Port | 2 bytes |
| Server Name | 32 bytes |
| Total | 39 bytes |

---

### RequestMessage
| Field | Size |
|------|------|
| Cookie ID | 4 bytes |
| Message Type | 1 byte |
| Number of Rounds | 1 byte |
| Client Name | 32 bytes |
| Total | 38 bytes |

---

### ClientPayloadMessage
Valid decisions:
- Hittt
- Stand

| Field | Size |
|------|------|
| Cookie ID | 4 bytes |
| Message Type | 1 byte |
| Decision | 5 bytes |
| Total | 10 bytes |

---

### ServerPayloadMessage
| Field | Size |
|------|------|
| Cookie ID | 4 bytes |
| Message Type | 1 byte |
| Round Status | 1 byte |
| Card Number | 2 bytes |
| Card Suit | 1 byte |
| Total | 9 bytes |

Round Status:
- 0 – Continue
- 1 – Tie
- 2 – Loss
- 3 – Win

---

## 4. Server Architecture

### MultiPlayer Server
- Single shared dealer
- Shared game state across players
- Synchronized rounds
- Player removal on disconnect

### BlackJackServer
- One dealer per client
- Thread-per-client model
- Isolated game state

---

## 5. Client Architecture
- UDP listener for offers
- TCP client for gameplay
- Blocking I/O model
- CLI-based interaction

---

## 6. Error Handling
- Message validation
- Corruption detection
- Timeout enforcement
- Graceful shutdown

---

## 7. Concurrency Model
- Server:
  - Broadcast thread
  - Client or table threads
- Client:
  - Single-threaded blocking execution

---

## 8. Future Improvements
- Graphical user interface
- Betting mechanics
- Soft Ace handling
- Encrypted communication
- Persistent leaderboards
