import Guacamole from 'guacamole-common-js';

console.log("✅ Obiekt Guacamole:", Guacamole);

const form = document.getElementById('connect-form');
const display = document.getElementById('display');

let client = null;
let socket = null;

form.addEventListener('submit', (e) => {
    e.preventDefault();

    // Pobieramy dane z formularza
    const protocol = document.getElementById('protocol').value;
    const hostname = document.getElementById('hostname').value;
    const port = document.getElementById('port').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Budujemy query z parametrami — zostanie dołączony przez connect()
    const query = `protocol=${protocol}&hostname=${hostname}&port=${port}&username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;
    const wsUrl = `ws://${window.location.host}/ws/guacamole/`;

    socket = new Guacamole.WebSocketTunnel(wsUrl)
    client = new Guacamole.Client(socket)

    const displayElement = client.getDisplay().getElement();
    display.innerHTML = '';
    display.appendChild(displayElement)

    // --- Klawiatura ---
    const keyboard = new Guacamole.Keyboard(document);

    keyboard.onkeydown = (keysym) => {
        client.sendKeyEvent(1, keysym);
    };

    keyboard.onkeyup = (keysym) => {
        client.sendKeyEvent(0, keysym);
    };

    // --- Myszka ---
    const mouse = new Guacamole.Mouse(displayElement);

    mouse.onmousedown =
    mouse.onmouseup =
    mouse.onmousemove = (mouseState) => {
        client.sendMouseState(mouseState);
    };

    // --- Stany i błędy ---
    client.onstatechange = (state) => {
        console.log("🔄 Stan klienta Guacamole:", state);
    };

    client.onerror = (error) => {
        console.error("❌ Błąd klienta Guacamole:", error);
    };

    // connect() dołącza query jako ?query do URL tunelu
    client.connect(query)

});