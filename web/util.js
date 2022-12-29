const under_node_js = typeof process !== "undefined" && process.release.name === "node"
if (under_node_js) {
  (async () => {
    const [,, code] = process.argv
    console.log(await eval(code))
  })()
}

const id = v => v
const noop = () => {}
const always = () => true

const repeat = (times, cb) => {
  for (let i = 0; i < times; ++i) cb()
}

const array_equals = (a, b) =>
  a.length === b.length &&
  a.every((v, i) => v === b[i])

const memoize = (fn) => {
  let cache = {}
  return (...args) => {
    let n = args[0] // just taking one argument here
    if (n in cache)
      return cache[n]

    const result = fn(n)
    cache[n] = result
    return result
  }
}

class SimpleWebsocket {
  static HANDLE_ONCE = "__once__"

  constructor(url = "ws://localhost:8080") {
    this.socket = new WebSocket(url)
    this.handlers = {}
    this.once_handlers = []
    this.socket.addEventListener("message", async ({data}) => {
      for (const json of data.trim().split("\n")) {
        const {evt_type, payload} = JSON.parse(json)
        console.log(`${evt_type} event received with payload:`)
        console.log(payload)
        if (evt_type in this.handlers)
          this.handlers[evt_type](payload)

        for (const cb of this.once_handlers)
          cb(payload)
        this.once_handlers = []
      }
    })
  }

  send(evt_type, payload = null) {
    if (this.socket.readyState === WebSocket.OPEN) {
      const json = JSON.stringify({evt_type, payload})
      this.socket.send(json)
    } else {
      this.socket.addEventListener("open", () => this.send(evt_type, payload))
    }
  }

  listen(evt_type, handler) {
    if (evt_type === SimpleWebsocket.HANDLE_ONCE)
      this.once_handlers.push(handler)
    else
      this.handlers[evt_type] = handler
  }
}

const ws_listen_send = (io, req_event, cb, resp_event) => {
  io.listen(req_event, async payload => {
    const res = await cb(payload)
    io.send(resp_event, res)
  })
}

const listen_once = (element, event_name, callback) => {
  return new Promise(resolve => {
    const listener = e => {
      const result = callback(e)
      if (!result) return
      element.removeEventListener(event_name, listener)
      resolve(result)
    }
    element.addEventListener(event_name, listener)
  })
}

const promise_timeout = (cb, delay) => new Promise(resolve =>
  setTimeout(() => resolve(cb()), delay))

const url_params = new URLSearchParams(window.location && window.location.search)
const q = (selector, element = document) => element.querySelector(selector)
const q_all = (selector, element = document) => Array.from(element.querySelectorAll(selector))

const append_element = (container, tag_name, options = {}) => {
  const el = document.createElement(tag_name, options)
  container.appendChild(el);
  return el
}

async function translate(query, target_lang) {
  const response = await fetch(`https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&dt=t&q=${query}&tl=${target_lang}`)
  const json = await response.json()
  return json[0][0][0]
}

function translate_nodes(nodes) {
  return Promise.all(Array.from(nodes).map(n => translate(n.textContent)))
}

