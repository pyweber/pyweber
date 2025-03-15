let socket;
let socketReady = false;
let messageQueue = [];

function connectWebSocket() {
    socket = new WebSocket('ws://localhost:8765');

    socket.onopen = function() {
        console.log('Connected to WebSocket!');
        socketReady = true;
        while (messageQueue.length > 0) {
            const message = messageQueue.shift();
            socket.send(message);
        }
    };

    socket.onerror = function(error) {
        console.error('Erro na conexão WebSocket:', error);
    };

    socket.onclose = function() {
        console.log('Websocket connection closed. Trying again in 1 second...');
        setTimeout(connectWebSocket, 1000);
        location.reload();
    };

    function fromBase64(base64) {
        return new TextDecoder().decode(Uint8Array.from(atob(base64), c => c.charCodeAt(0)));
    };

    socket.onmessage = function(event) {
        if (event.data === 'reload') {
            location.reload();
        } else {
            const data = JSON.parse(event.data);
            if (data.template) {
                const decodedHTML = fromBase64(data.template);
                const parser = new DOMParser();
                const doc = parser.parseFromString(decodedHTML, 'text/html');
                document.body.innerHTML = doc.body.outerHTML
            } else if (data.Error) {
                console.log(data)
            };
        }
    };

    return socket
}

function sendEvent(type, event) {
    function toBase64(string) {
        const encoder = new TextEncoder();
        const encoded = encoder.encode(string);
        let binary = '';
        encoded.forEach(byte => binary += String.fromCharCode(byte));
        return btoa(binary);
    }

    function getFormValues() {
        const values = {};
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            const id = input.getAttribute('uuid');
            if (id) {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    values[id] = input.value;

                    if (input.checked) {
                        input.setAttribute('checked', '');
                    } else {
                        input.removeAttribute('checked');
                    }
                } else if (input.tagName === 'SELECT') {
                    values[id] = input.value;

                    const options = input.querySelectorAll('option');
                    options.forEach(option => {
                        if (option.value === input.value) {
                            option.setAttribute('selected', '');
                        } else {
                            option.removeAttribute('selected');
                        }
                        values[id] = option.value;
                    });
                } else {
                    values[id] = input.value;
                }
            }
        });

        return values;
    }

    const DOMBase64 = toBase64(document.documentElement.outerHTML);
    const target = event.target instanceof HTMLElement ? event.target : null;

    const eventData = {
        type: type,
        route: window.location.pathname,
        target_uuid: target ? target.getAttribute("uuid") : null,
        template: DOMBase64,
        values: toBase64(JSON.stringify(getFormValues())),
        event_data: {
            clientX: event.clientX || null,
            clientY: event.clientY || null,
            key: event.key || null,
            deltaX: event.deltaX || null,
            deltaY: event.deltaY || null,
            touches: event.touches ? event.touches.length : null,
            timestamp: Date.now()
        },
    };

    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(eventData));
    } else {
        messageQueue.push(JSON.stringify(eventData));
        console.log('Aguardando conexão...');
    }
}

function trackEvents() {
    const events = [
        // Eventos de Mouse
        "click", "dblclick", "mousedown", "mouseup", "mousemove", "mouseover", "mouseout",
        "mouseenter", "mouseleave", "contextmenu", "wheel",

        // Eventos de Teclado
        "keydown", "keyup", "keypress",

        // Eventos de Formulário
        "focus", "blur", "change", "input", "submit", "reset", "select",

        // Eventos de Drag & Drop
        "drag", "dragstart", "dragend", "dragover", "dragenter", "dragleave", "drop",

        // Eventos de Scroll e Resize
        "scroll", "resize",

        // Eventos de Mídia
        "play", "pause", "ended", "volumechange", "seeked", "seeking", "timeupdate",

        // Eventos de Rede
        "online", "offline",

        // Eventos de Toque (Mobile)
        "touchstart", "touchmove", "touchend", "touchcancel"
    ];

    events.forEach(eventType => {
        document.addEventListener(eventType, (event) => sendEvent(eventType, event));
    });
}

connectWebSocket();
trackEvents();