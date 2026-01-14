# Multiplayer Blackjack – Client Server Application

## Overview
This project implements a **network-based Blackjack game** using a **client–server architecture** in Python.
It supports **automatic server discovery**, **reliable gameplay communication**, and **simultaneous players**.

Two different server models are implemented to demonstrate alternative concurrency designs:

1. **MultiPlayer Server** – multiple players play **together on the same Blackjack table**
2. **BlackJackServer** – multiple players play **independently**, each with their **own dealer**

The project focuses on networking, protocol design, concurrency, and robustness rather than UI.

---

## Key Features
- UDP broadcast–based server discovery
- TCP-based reliable gameplay communication
- Custom fixed-size binary protocol
- Multiplayer synchronization
- Threaded server execution
- Timeout and disconnect handling
- Deterministic Blackjack game flow

---

## Server Implementations

### 1. MultiPlayer Server (`MultiPlayer.py`)
- Multiple clients join **the same table**
- A **single dealer** serves all players
- Players play **simultaneously within the same rounds**
- Dealer actions affect all players consistently
- Supports players joining and leaving safely

This implementation demonstrates:
- Shared game state
- Multiplayer coordination
- Server-side synchronization logic

---

### 2. Single-Client Threaded Server (`BlackJackServer.py`)
- Each client gets:
  - A **dedicated dealer**
  - An **independent game session**
- Each client runs in its **own thread**
- Clients do not affect one another

This implementation demonstrates:
- Thread-per-client server design
- Isolation of game state
- Simplified game logic

---

## Project Structure

```
.
├── BlackJackClient.py    # Client logic and user interaction
├── BlackJackServer.py    # Threaded single-client server
├── MultiPlayer.py        # Shared-table multiplayer server
├── Dealer.py             # Card, deck, and scoring logic
├── Messages.py           # Binary protocol definitions
├── README.md
└── architecture.md
```

---

## Communication Model

### UDP – Discovery Phase
- Servers broadcast offers every second
- Clients listen on a known UDP port
- No hardcoded server IPs are required

### TCP – Gameplay Phase
- Client connects to selected server
- All gameplay messages are sent over TCP
- Messages are read using `recv_exact_tcp` to ensure integrity

---

## Message Protocol Summary
All protocol messages:
- Have fixed sizes
- Include a cookie ID
- Include a message type
- Are validated before processing

Main message types:
- `OfferMessage`
- `RequestMessage`
- `ClientPayloadMessage`
- `ServerPayloadMessage`

Full protocol details are documented in `architecture.md`.

---

## Game Rules
- Standard Blackjack scoring:
  - Ace = 11
  - Face cards = 10
- Dealer hits until reaching at least 17
- Round results:
  - Win
  - Loss
  - Tie

---

## Running the Project

### Start a Server

#### Shared Multiplayer Table
```bash
python MultiPlayer.py
```

#### Independent Client Sessions
```bash
python BlackJackServer.py
```

---

### Start the Client
```bash
python BlackJackClient.py
```

The client will:
1. Ask for a player name
2. Listen for server offers
3. Allow selecting a server
4. Play the requested number of rounds

---

## Error Handling and Robustness
- Invalid or corrupted messages are rejected
- Timeouts prevent blocked sockets
- Unexpected client disconnects are handled gracefully
- Fixed-size reads prevent partial-message bugs

---

## Limitations
- Command-line interface only
- No betting system
- No persistent player state
- Ace value is fixed (no soft Ace handling)

---

## Educational Purpose
This project was developed as an academic exercise to demonstrate:
- Network programming principles
- Multiplayer server architectures
- Binary protocol design
- Concurrent server execution models
