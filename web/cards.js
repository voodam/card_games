const TEXT_DELAY_MS = url_params.get("text_delay") || 3000
const SHOW_HAND_DELAY_MS = url_params.get("show_hand_delay") || 5000
const TABLE_CLEAR_DELAY_MS = url_params.get("table_clear_delay") || 3000

class Deck {
  constructor(container) {
    this.container = container
    this.delay = false
    this.after_delay = []
  }

  add(card) {
    if (this.delay)
      this.after_delay.push(() => this.add(card))
    else
      this.container.appendChild(card)
  }

  clear() {
    this.container.textContent = ""
  }

  clear_delayed(delay_ms) {
    this.delay = true

    setTimeout(() => {
      this.delay = false
      this.clear()
      for (const cb of this.after_delay)
        cb()
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
  image.src = `img/cards/${suit}_${rank}.png`
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

const listen_showhide = (io, hand, req_event, cb, resp_event) =>
  ws_listen_send(io, req_event, async payload => {
    await show_hand(hand)
    // Async JS works badly with blocking standart popups (confirm and prompt functions),
    // timeout mostly solves this problem.
    const res = await promise_timeout(() => cb(payload), 100)
    hide_hand(hand)
    return res
  }, resp_event)

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

const mbox = new MessageBox(q("#mbox"))
const table = new Deck(q("#table"))
const trump = new Deck(q("#trump"))

const common_events = io => {
  io.listen(EvtType.TRICK, () => table.clear_delayed(TABLE_CLEAR_DELAY_MS))
  io.listen(EvtType.TRUMP, suit => deck_set(trump, create_ace(suit)))
  io.listen(EvtType.CARD, ({from, card: {rank, suit}}) => table.add(create_card(rank, suit, from)))
}

const personal_events = io => {
  const hand = new Deck(create_hand(name))

  io.listen(EvtType.TEXT, text => mbox.show_text(text))
  io.listen(EvtType.DEAL, cards => {
    deck_set_all(hand, cards.map(({rank, suit}) => create_card(rank, suit)))
  })

  listen_showhide(io, hand, EvtType.SELECT_YESNO, confirm, EvtType.SELECT_YESNO_RESPONSE)
  listen_showhide(io, hand, EvtType.SELECT_BID, input_bid, EvtType.SELECT_BID_RESPONSE)

  listen_showhide(io, hand, EvtType.SELECT_CARD, async allowed_cards => {
    const card = await hand.select_card(allowed_cards)
    card.remove()
    return card.dataset
  }, EvtType.SELECT_CARD_RESPONSE)

  listen_showhide(io, hand, EvtType.SELECT_SUIT, async suits => {
    deck_set_all(table, suits.map(create_ace))
    const card = await table.select_card()
    table.clear()
    return card.dataset.suit
  }, EvtType.SELECT_SUIT_RESPONSE)
}

