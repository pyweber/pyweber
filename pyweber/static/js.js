let socket;
let socketReady = false;

const EventRef = new Proxy(
    {DOCUMENT: 'document', WINDOW: 'window'},
    {set(target, prop, value) {
            throw new Error(`Cannot modified constant ${prop}`);
        }
    }
);

function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.hostname;
    const wsPort = window.PYWEBER_WS_PORT || 8765;
    socket = new WebSocket(`${wsProtocol}//${wsHost}:${wsPort}`);

    socket.onopen = function() {
        console.log('Connected to WebSocket!');
        socketReady = true;
        socket.send(JSON.stringify(getEventData({})));
    };

    socket.onerror = function(error) {
        console.error('Erro with Websocket connection:', error);
    };

    socket.onclose = function() {
        console.log('Websocket connection closed. Trying again in 1 second...');
        setTimeout(connectWebSocket, 1000);
        location.reload();
    };

    socket.onmessage = function(event) {
        if (event.data === 'reload') {
            location.reload();
            return
        };

        const data = JSON.parse(event.data);
        if (data.setSessionId) {
            setSessionId(data.setSessionId);
            return;

        };
        
        if (data.template) {
            const decodedHTML = data.template;
            const parser = new DOMParser();
            const doc = parser.parseFromString(decodedHTML, 'text/html');
            document.body.innerHTML = doc.body.outerHTML

        } else if (data.Error) {
            console.log(data)
        };
    };

    return socket
}

function getsessionId() {
    return sessionStorage.getItem('_pyweber_sessionId') || null;
}

function setSessionId(sessionId) {
    if (!getsessionId()) {
        sessionStorage.setItem('_pyweber_sessionId', sessionId);
    }
}

function sendEvent({type, event, event_ref}) {
    const target = event.target instanceof HTMLElement ? event.target : null;
    const eventData = getEventData({type, event, event_ref});

    if (socket.readyState === WebSocket.OPEN) {
        if (target) {
            if (target.getAttribute(`_on${type}`)) {
                socket.send(JSON.stringify(eventData));
            };
        };
    };
}

function toBase64(string) {
    const encoder = new TextEncoder();
    const encoded = encoder.encode(string);
    let binary = '';
    encoded.forEach(byte => binary += String.fromCharCode(byte));
    return btoa(binary);
};

function fromBase64(base64) {
    return new TextDecoder().decode(Uint8Array.from(atob(base64), c => c.charCodeAt(0)));
};

function getEventData({type=null, event=null, event_ref=null}) {
    let target;

    if (event){
        target = event.target instanceof HTMLElement ? event.target : null;
    };

    const eventData = {
        type: type,
        event_ref: event_ref,
        route: window.location.pathname,
        target_uuid: target?.getAttribute("uuid") ?? null,
        template: document.documentElement.outerHTML,
        values: JSON.stringify(getFormValues()),
        event_data: {
            clientX: event?.clientX ?? null,
            clientY: event?.clientY ?? null,
            key: event?.key ?? null,
            deltaX: event?.deltaX ?? null,
            deltaY: event?.deltaY ?? null,
            touches: event?.touches?.length ?? null,
            timestamp: Date.now()
        },
        window_data: JSON.stringify(getWindowData()),
        sessionId: getsessionId()
    };

    return eventData;
}

function getWindowData() {
    // Captura as informações da janela
    const windowData = {
        // Dimensões da janela
        width: window.outerWidth,
        height: window.outerHeight,
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
        scrollX: window.scrollX,
        scrollY: window.scrollY,

        // Informações de localização (URL)
        location: {
            href: window.location.href,
            protocol: window.location.protocol,
            host: window.location.host,
            port: window.location.port,
            pathname: window.location.pathname,
            origin: window.location.origin
        },

        // Informações de armazenamento
        localStorage: JSON.stringify(localStorage),
        sessionStorage: JSON.stringify(sessionStorage),

        // Informações de tela
        screen: {
            width: window.screen.width,
            height: window.screen.height,
            colorDepth: window.screen.colorDepth,
            pixelDepth: window.screen.pixelDepth,
            screenX: window.screen.screenX,
            screenY: window.screen.screenY,
            orientation: {
                angle: window.screen.orientation.angle,
                type: window.screen.orientation.type,
                on_change: window.screen.orientation.onchange
            }
        }
    };

    return windowData;
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

function trackEvents() {
    const documentEvents = [
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

        // Eventos de Toque (Mobile)
        "touchstart", "touchmove", "touchend", "touchcancel"
    ];

    const windowEvents = [
        // Eventos de Janela e Navegação
        "afterprint", "beforeprint", "beforeunload", "hashchange", "load", "pageshow", "pagehide", "popstate", "resize", "scroll", "DOMContentLoaded",
    
        // Eventos de Foco e Blur
        "focus", "blur",
    
        // Eventos de Rede
        "online", "offline",
    
        // Eventos de Armazenamento
        "storage",
    
        // Eventos de Mensagens e Comunicação
        "message", "messageerror",
    
        // Eventos de Mídia e Recursos
        "error", "abort", "loadstart", "progress", "loadend", "timeout",
    
        // Eventos de Animação e Transição
        "animationstart", "animationend", "animationiteration", "transitionstart", "transitionend", "transitioncancel",
    
        // Eventos de Fullscreen e Pointer Lock
        "fullscreenchange", "fullscreenerror", "pointerlockchange", "pointerlockerror",
    
        // Eventos de Dispositivo
        "devicemotion", "deviceorientation", "deviceorientationabsolute",
    
        // Eventos de Gamepad
        "gamepadconnected", "gamepaddisconnected",
    
        // Eventos de Service Worker e Cache
        "install", "activate", "fetch", "message", "messageerror", "notificationclick", "notificationclose", "push", "pushsubscriptionchange", "sync", "periodicsync", "backgroundfetchsuccess", "backgroundfetchfailure", "backgroundfetchabort", "backgroundfetchclick", "contentdelete",
    
        // Eventos de Clipboard
        "cut", "copy", "paste",
    
        // Eventos de Seleção de Texto
        "select", "selectionchange",
    
        // Eventos de Formulário
        "submit", "reset", "input", "change", "invalid", "search", "toggle", "formdata",
    
        // Eventos de Mídia (Áudio/Video)
        "play", "pause", "ended", "volumechange", "seeked", "seeking", "timeupdate", "canplay", "canplaythrough", "cuechange", "durationchange", "emptied", "loadeddata", "loadedmetadata", "loadstart", "stalled", "suspend", "waiting",
    
        // Eventos de Toque (Mobile)
        "touchstart", "touchend", "touchmove", "touchcancel",
    
        // Eventos de Pointer (Mouse/Touch)
        "pointerover", "pointerenter", "pointerdown", "pointermove", "pointerup", "pointercancel", "pointerout", "pointerleave", "gotpointercapture", "lostpointercapture",
    
        // Eventos de Drag & Drop
        "drag", "dragstart", "dragend", "dragover", "dragenter", "dragleave", "drop",
    
        // Eventos de Teclado
        "keydown", "keyup",
    
        // Eventos de Composição (IME)
        "compositionstart", "compositionupdate", "compositionend",
    
        // Eventos de Visibilidade
        "visibilitychange",
    
        // Eventos de Rejeição de Promises
        "rejectionhandled", "unhandledrejection",
    
        // Eventos de Segurança
        "securitypolicyviolation"
    ];

    documentEvents.forEach(eventType => {
        document.addEventListener(eventType, (event) => sendEvent({type: eventType, event: event, event_ref: EventRef.DOCUMENT}));
    });

    windowEvents.forEach(eventType => {
        window.addEventListener(eventType, (event) => sendEvent({type: eventType, event: event, event_ref: EventRef.WINDOW}));
    });
}

connectWebSocket();
trackEvents();