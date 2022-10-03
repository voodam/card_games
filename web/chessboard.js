const EvtType = {
  // to client
  BOARD_PLACE: "BOARD_PLACE",
  BOARD_REMOVE: "BOARD_REMOVE",
  SELECT_BOARD_MOVE: "SELECT_BOARD_MOVE",
  SELECT_PROMOTION: "SELECT_PROMOTION",
  // to server
  ENTER: "ENTER",
  SELECT_BOARD_MOVE_RESPONSE: "SELECT_BOARD_MOVE_RESPONSE",
  SELECT_PROMOTION_RESPONSE: "SELECT_PROMOTION_RESPONSE"
}

const params = new URLSearchParams(location.search)
const WEBSOCKET_URL = params.get("websocket_url") || `ws://${location.hostname}:8080`

class Board {
  constructor(container) {
    this.container = container
    this.x_size = q_all("tr:nth-child(1) td").length
    this.y_size = q_all("tr", container).length
  }

  place(piece, [x, y]) {
    this._get_cell(x, y).textContent = piece
  }

  remove([x, y]) {
    this._get_cell(x, y).textContent = ""
  }

  async select_move() {
    const get_cell = target => {
      if (target.tagName == "TD") target = target.firstChild
      if (target.tagName !== "DIV") target = null
      return target
    } 

    const from = await listen_once(this.container, "click", ({target}) => {
      const cell = get_cell(target)
      if (!cell || !cell.textContent) return null
      return this._get_coords(cell)
    })
    const to = await listen_once(this.container, "click", ({target}) => {
      const cell = get_cell(target)
      if (!cell) return null
      const coords = this._get_coords(cell)
      if (array_equals(from, coords)) return null
      return coords
    })

    return [from, to]
  }

  _get_cell(x, y) {
    console.assert(x >= 0 && x <= this.x_size - 1, x)
    console.assert(y >= 0 && y <= this.y_size - 1, y)
    const selector = `tr:nth-child(${this.y_size - y}) td:nth-child(${x + 1}) div`
    return q(selector, this.container)
  }

  _get_coords(cell) {
    const td = cell.parentElement
    const tr = td.parentElement
    const row = Array.from(tr.children)
    const x = row.indexOf(td)
    const rows = Array.from(tr.parentElement.children)
    const y = this.y_size - rows.indexOf(tr) - 1
    return [x, y]
  }
}

const board = new Board(q("#board"))

const common_events = io => {
  io.listen(EvtType.BOARD_PLACE, ({piece, coords}) => board.place(piece, coords))
  io.listen(EvtType.BOARD_REMOVE, coords => board.remove(coords))
}

const personal_events = io => {
  ws_listen_send(io, EvtType.SELECT_BOARD_MOVE, () => board.select_move(), EvtType.SELECT_BOARD_MOVE_RESPONSE)
  ws_listen_send(io, EvtType.SELECT_PROMOTION, piece_types => "♛", EvtType.SELECT_PROMOTION_RESPONSE)
}

