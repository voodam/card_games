const EvtType = {
  // to client
  TEXT: "TEXT",
  GAME: "GAME",
  TRICK: "TRICK",
  DEAL: "DEAL",
  TRUMP: "TRUMP",
  CARD: "CARD",
  SELECT_YESNO: "SELECT_YESNO",
  SELECT_BID: "SELECT_BID",
  SELECT_CARD: "SELECT_CARD",
  SELECT_SUIT: "SELECT_SUIT",
  // to server
  ENTER: "ENTER",
  SELECT_YESNO_RESPONSE: "SELECT_YESNO_RESPONSE",
  SELECT_BID_RESPONSE: "SELECT_BID_RESPONSE",
  SELECT_CARD_RESPONSE: "SELECT_CARD_RESPONSE",
  SELECT_SUIT_RESPONSE: "SELECT_SUIT_RESPONSE"
}

const params = new URLSearchParams(location.search)
const TEXT_DELAY_MS = params.get("text_delay") || 3000
const SHOW_HAND_DELAY_MS = params.get("show_hand_delay") || 5000
const TABLE_CLEAR_DELAY_MS = params.get("table_clear_delay") || 3000
const WEBSOCKET_URL = params.get("websocket_url") || `ws://${location.hostname}:8080`

class Deck {
  constructor(container) {
    this.container = container
    this.delay = false
    this.after_delay = []
  }

  add(card) {
    if (this.delay) {
      this.after_delay.push(() => this.add(card))
      return
    }
    this.container.appendChild(card)
  }

  clear() {
    this.container.textContent = ""
  }

  clear_delayed(delay_ms) {
    this.delay = true
    setTimeout(() => {
      this.clear()
      this.delay = false
      for (const callback of this.after_delay)
        callback()
      this.after_delay = []
    }, delay_ms)
  }

  async select_card(cards = []) {
    const key = c => `${c.rank}_${c.suit}`
    const allowed_cards = new Set(cards.map(key))

    return listen_once(this.container, "click", e => {
      if (e.composedPath()[0].tagName !== "IMG") return null
      const card = e.composedPath()[1]
      if (allowed_cards.size && !allowed_cards.has(key(card.dataset))) return null
      return card
    })
  }
}

const deck_set = (deck, card) => {
  deck.clear()
  deck.add(card)
}

const deck_set_all = (deck, cards) => {
  deck.clear()
  for(const card of cards)
    deck.add(card)
}

const create_card = (rank, suit, title = "") => {
  const container = document.createElement("div")
  const image = document.createElement("img")
  image.src = `img/${suit}_${rank}.png`
  const title_container = document.createElement("div")
  title_container.textContent = title

  container.dataset.rank = rank
  container.dataset.suit = suit
  container.classList.add("card")
  container.appendChild(title_container)
  container.appendChild(image)
  return container
}

const create_ace = suit => create_card("A", suit)

const create_hand = (name) => {
  const hand = document.createElement("div")
  hand.dataset.player = name
  hand.classList.add("hand")
  hand.style.display = "none"
  document.body.appendChild(hand)
  return hand
}

const show_hand = hand => {
  if (q_all(".hand").length <= 1) {
    hand.container.style.display = "flex"
    return
  }

  return promise_timeout(() => {
    hand.container.style.display = "flex"
  }, SHOW_HAND_DELAY_MS)
}

const hide_hand = hand => {
  if (q_all(".hand").length > 1)
    hand.container.style.display = "none"
}

class MessageBox {
  constructor(container) {
    this.container = container
    this.queue = []
  }

  show_text(text) {
    if (this.queue[this.queue.length-1] !== text)
      this.queue.push(text)

    if (this.queue.length === 1)
      this._run_queue()
  }

  _run_queue() {
    const text = this.queue[0]
    if (text === undefined) return
    this.container.textContent = text

    setTimeout(() => {
      this.queue.shift()
      this._run_queue()
    }, TEXT_DELAY_MS)
  }
}

const listen_event_showhide = (io, hand, req_event, cb, resp_event) =>
  io.listen_event(req_event, async payload => {
    await show_hand(hand)
    const res = await cb(payload)
    hide_hand(hand)
    io.send_event(resp_event, res)
  })

const input_bid = ({min_bid, max_bid, step, can_skip, message}) => {
  let bid
  do {
    const str = prompt(message)
    if (can_skip && (str === "" || str === null))
      return null
    bid = parseInt(str)
  } while (bid < min_bid || bid > max_bid || bid % step !== 0)
  return bid
}

const enter_container = q("#enter")
const mbox = new MessageBox(q("#mbox"))
const table = new Deck(q("#table"))
const trump = new Deck(q("#trump"))
let is_first_enter = true

const enter = button => {
  button.remove()
  const name = button.value
  const io = new SimpleWebsocket(WEBSOCKET_URL)
  io.send_event(EvtType.ENTER, name)
  const hand = new Deck(create_hand(name))

  if (is_first_enter) {
    is_first_enter = false
    // same events for all players
    io.listen_event(EvtType.TRICK, () => table.clear_delayed(TABLE_CLEAR_DELAY_MS))
    io.listen_event(EvtType.TRUMP, suit => deck_set(trump, create_ace(suit)))
    io.listen_event(EvtType.CARD, ({from, card: {rank, suit}}) => table.add(create_card(rank, suit, from)))
  }

  io.listen_event(EvtType.TEXT, text => mbox.show_text(text))
  io.listen_event(EvtType.DEAL, cards => {
    enter_container.remove()
    deck_set_all(hand, cards.map(({rank, suit}) => create_card(rank, suit)))
  })
  // i don't know why timeout is required to hand can be shown
  listen_event_showhide(io, hand, EvtType.SELECT_YESNO,
    message => promise_timeout(() => confirm(message), 1),
    EvtType.SELECT_YESNO_RESPONSE)
  listen_event_showhide(io, hand, EvtType.SELECT_BID,
    payload => promise_timeout(() => input_bid(payload), 1),
    EvtType.SELECT_BID_RESPONSE)
  listen_event_showhide(io, hand, EvtType.SELECT_CARD, async allowed_cards => {
    const card = await hand.select_card(allowed_cards)
    card.remove()
    return card.dataset
  }, EvtType.SELECT_CARD_RESPONSE)
  listen_event_showhide(io, hand, EvtType.SELECT_SUIT, async suits => {
    deck_set_all(table, suits.map(create_ace))
    const card = await table.select_card()
    table.clear()
    return card.dataset.suit
  }, EvtType.SELECT_SUIT_RESPONSE)
}

