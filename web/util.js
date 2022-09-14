const under_node_js = typeof process !== "undefined" && process.release.name === "node"
if (under_node_js) {
  (async () => {
    const [,, code] = process.argv
    console.log(await eval(code))
  })()
}

class SimpleWebsocket {
  constructor(url = "ws://localhost:8080") {
    this.socket = new WebSocket(url)
    this.handlers = {}
    this.socket.addEventListener("message", async ({data}) => {
      for (const json of data.trim().split("\n")) {
        const {evt_type, payload} = JSON.parse(json)
        console.log(`${evt_type} event received with payload:`)
        console.log(payload)
        if (evt_type in this.handlers)
          this.handlers[evt_type](payload)
      }
    })
  }

  send_event(evt_type, payload = null) {
    if (this.socket.readyState == WebSocket.OPEN) {
      const json = JSON.stringify({evt_type, payload})
      this.socket.send(json)
    } else {
      this.socket.addEventListener("open", () => this.send_event(evt_type, payload))
    }
  }

  listen_event(evt_type, handler) {
    this.handlers[evt_type] = handler
  }
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

const q = (selector, element = document) => element.querySelector(selector)
const q_all = (selector, element = document) => Array.from(element.querySelectorAll(selector))

async function translate(query, target_lang) {
  const response = await fetch(`https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&dt=t&q=${query}&tl=${target_lang}`)
  const json = await response.json()
  return json[0][0][0]
}

function translate_nodes(nodes) {
  return Promise.all(Array.from(nodes).map(n => translate(n.textContent)))
}

