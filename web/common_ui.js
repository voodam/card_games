const create_enter_buttons = (buttons_container, click_handler) => {
  const create_button = player => {
    const input = document.createElement("input")
    input.type = "button"
    input.value = player
    input.style = "font-size: 70px"
    input.onclick = ({target}) => click_handler(target)
    return input
  }

  const players = url_params.getAll("player")
  for (const p of players)
    buttons_container.appendChild(create_button(p))
}

const enter_click_handler = (buttons_container, websocket_url, personal_events_cb, common_events_cb = id) => {
  const cb = button => {
    button.remove()
    const name = button.value
    const io = new SimpleWebsocket(websocket_url)
    io.send(EvtType.ENTER, name)
    io.listen(SimpleWebsocket.HANDLE_ONCE, () => buttons_container.remove())

    if (!cb.common_events_cb) {
      common_events_cb(io)
      cb.common_events_cb = true
    }
    personal_events_cb(io)
  }
  return cb
}

