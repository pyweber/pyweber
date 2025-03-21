let socket;
let socketReady = false;
let messageQueue = [];
let event_ref = "document" || "window"

function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.hostname;
    const wsPort = window.PYWEBER_WS_PORT || 8765;
    socket = new WebSocket(`${wsProtocol}//${wsHost}:${wsPort}`);

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

function sendEvent(type, event, event_ref) {
    function toBase64(string) {
        const encoder = new TextEncoder();
        const encoded = encoder.encode(string);
        let binary = '';
        encoded.forEach(byte => binary += String.fromCharCode(byte));
        return btoa(binary);
    }

    function getWindowData() {
        // Captura as informações da janela
        const windowData = {
            // Dimensões da janela
            width: window.innerWidth,
            height: window.innerHeight,
            outerWidth: window.outerWidth,
            outerHeight: window.outerHeight,
            scrollX: window.scrollX,
            scrollY: window.scrollY,
            screenX: window.screenX,
            screenY: window.screenY,
    
            // Informações de localização (URL)
            location: {
                href: window.location.href,
                protocol: window.location.protocol,
                host: window.location.host,
                hostname: window.location.hostname,
                port: window.location.port,
                pathname: window.location.pathname,
                search: window.location.search,
                hash: window.location.hash,
            },
    
            // Informações do navegador
            navigator: {
                userAgent: navigator.userAgent,
                userAgentData: navigator.userAgentData ? navigator.userAgentData : null,
                language: navigator.language,
                cookieEnabled: navigator.cookieEnabled,
            },
    
            // Informações de armazenamento
            localStorage: JSON.stringify(localStorage),
            sessionStorage: JSON.stringify(sessionStorage),
    
            // Histórico de navegação (simplificado)
            history: window.history.length,
    
            // Informações de desempenho (se disponível)
            performance: window.performance ? {
                timing: window.performance.getEntriesByType('navigation')[0] || null,
            } : null,
    
            // Informações de tela
            screen: {
                width: window.screen.width,
                height: window.screen.height,
                colorDepth: window.screen.colorDepth,
                pixelDepth: window.screen.pixelDepth,
            },
    
            // Informações de dispositivos (se disponível)
            devicePixelRatio: window.devicePixelRatio,
            orientation: window.screen.orientation ? window.screen.orientation.type : null,
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

    const target = event.target instanceof HTMLElement ? event.target : null;

    const eventData = {
        type: type,
        event_ref: event_ref,
        route: window.location.pathname,
        target_uuid: target ? target.getAttribute("uuid") : null,
        template: toBase64(document.documentElement.outerHTML),
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
        window_data: toBase64(JSON.stringify(getWindowData()))
    };

    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(eventData));
    } else {
        messageQueue.push(JSON.stringify(eventData));
        console.log('Aguardando conexão...');
    }
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
        "afterprint", "beforeprint", "beforeunload", "hashchange", "load", "unload", "pageshow", "pagehide", "popstate", "resize", "scroll", "DOMContentLoaded",
    
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
        "devicemotion", "deviceorientation", "deviceorientationabsolute", "orientationchange",
    
        // Eventos de Gamepad
        "gamepadconnected", "gamepaddisconnected",
    
        // Eventos de VR
        "vrdisplayconnect", "vrdisplaydisconnect", "vrdisplaypresentchange", "vrdisplayactivate", "vrdisplaydeactivate", "vrdisplayblur", "vrdisplayfocus", "vrdisplaypointerrestricted", "vrdisplaypointerunrestricted",
    
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
        "keydown", "keyup", "keypress",
    
        // Eventos de Composição (IME)
        "compositionstart", "compositionupdate", "compositionend",
    
        // Eventos de Impressão
        "beforeprint", "afterprint",
    
        // Eventos de Visibilidade
        "visibilitychange",
    
        // Eventos de Rejeição de Promises
        "rejectionhandled", "unhandledrejection",
    
        // Eventos de Segurança
        "securitypolicyviolation"
    ];

    documentEvents.forEach(eventType => {
        document.addEventListener(eventType, (event) => sendEvent(eventType, event, "document"));
    });

    windowEvents.forEach(eventType => {
        window.addEventListener(eventType, (event) => sendEvent(eventType, event, "window"));
    });
}

connectWebSocket();
trackEvents();