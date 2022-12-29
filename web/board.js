class Board {
  constructor(container) {
    this.container = container
    this._x_size = memoize(() => q_all("tr:nth-child(1) td", container).length)
    this._y_size = memoize(() => q_all("tr", container).length)
  }

  place(piece, [x, y]) {
    this._get_cell(x, y).textContent = piece
  }

  remove([x, y]) {
    this._get_cell(x, y).textContent = ""
  }

  async select_from_to() {
    const from = await this.select_cell(cell => cell.textContent)
    const to = await this.select_cell((_, coords) => !array_equals(from, coords))
    return [from, to]
  }

  select_cell(filter_cell_cb = always) {
    const get_cell = target => {
      if (target.tagName == "TD") target = target.firstChild
      if (target.tagName === "DIV") return target
      return null
    }

    return listen_once(this.container, "click", ({target}) => {
      const cell = get_cell(target)
      if (!cell) return null
      const coords = this._get_coords(cell)
      if (!filter_cell_cb(cell, coords)) return null
      return coords
    })
  }

  _get_cell(x, y) {
    console.assert(x >= 0 && x <= this._x_size() - 1, x)
    console.assert(y >= 0 && y <= this._y_size() - 1, y)
    const selector = `tr:nth-child(${this._y_size() - y}) td:nth-child(${x + 1}) div`
    return q(selector, this.container)
  }

  _get_coords(cell) {
    const td = cell.parentElement
    const tr = td.parentElement
    const row = Array.from(tr.children)
    const x = row.indexOf(td)
    const rows = Array.from(tr.parentElement.children)
    const y = this._y_size() - rows.indexOf(tr) - 1
    return [x, y]
  }
}

class BoardGame {
  constructor(board) {
    this.board = board
  }

  common_events(io) {
    io.listen(EvtType.FIELD_PLACE, ({unit, coords}) => this.board.place(unit, coords))
    io.listen(EvtType.FIELD_REMOVE, coords => this.board.remove(coords))
  }

  personal_events(io) {
    ws_listen_send(io, EvtType.SELECT_FIELD_MOVE, () => this.select_move(), EvtType.SELECT_FIELD_MOVE_RESPONSE)
  }

  select_move() {}

  board_size() {
    return [8, 8]
  }
}

const games = {
  chess: class extends BoardGame {
    personal_events(io) {
      super.personal_events(io)
      ws_listen_send(io, EvtType.SELECT_PROMOTION, unit_types => "♛", EvtType.SELECT_PROMOTION_RESPONSE)
    }

    select_move() {
      return this.board.select_from_to()
    }
  },

  battleship: class extends BoardGame {
    select_move() {
      return this.board.select_cell()
    }
  }
}

const game_name = url_params.get("game") || "chess"
const board = new Board(q("#board"))
const game = new games[game_name](board)

