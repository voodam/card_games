Game framework allowing easily add new games (I hope), minimal and simple design.

### Current games implemented
- Card:
  * [1000](https://en.wikipedia.org/wiki/1000_(card_game))
  * [Durak](https://en.wikipedia.org/wiki/Durak)
  * Kozel
- Board:
  * [Chess](https://en.wikipedia.org/wiki/Chess)
  * [Checkers](https://en.wikipedia.org/wiki/Checkers)

### Features
- WebSocket based Web frontend
- Blocking socket API is used, WebSocket messages are retranslated to socket via `websocat`
- Reconnection without server restart
- Console client
- CPU random-moving players (good for testing)

### Requirements
- `simple-term-menu` python package if you'll use console client
- `websockat` linux tool if you'll use web client

### Assumptions
- App is not scaling on a large number of users (otherwise async API should be used at least)
- Game is turn-based: at every moment of time only one player is active
- Minimalistic interface (basically I just wanted to write game logic with minimal effort, not sophisticated frontend)

### Layer structure
- `lib`: general purpose python utils
- `logic`: game logic common library
- `logic.game`: game logic of every specific game
- `logic.io`: reusable components for client communication (socket, web, console, AI etc.)
- clients: `web`, `socket_client.py`
- root: game servers using all components and tests
