let socket;
let socketReady = false;
let window_event_received = false;
const earyEventsBuffer = [];

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
    const maxReconnectAttempts = 2
    let reconnectAttemps = 0
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
        if (reconnectAttemps <= maxReconnectAttempts) {
            reconnectAttemps ++;
            console.log('Websocket connection closed. Trying again in 1 second...');
            setTimeout(connectWebSocket, 1000);
            location.reload();
        };
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);

        if (data.window) {
            Object.keys(sessionStorage).forEach(item => {
                if (item !== '_pyweber_sessionId') {
                    sessionStorage.removeItem(item)
                };
            });

            for (let i=0; i<data.window.length; i++) {
                palavra = data.window[i].replace(/^_on/, "");
                evt = palavra.split("_")[0];
                sessionStorage.setItem(evt, data.window[i]);
            };

            if (!window_event_received) {
                window_event_received = true;
                earyEventsBuffer.forEach(item => {
                    sendEvent(item);
                });
                earyEventsBuffer.length = 0;
            }
        };

        if (data.template) {
            applyDifferences(data.template);
            return;
        };

        if (data.reload) {
            location.reload();
            return;
        };

        if (data.setSessionId) {
            setSessionId(data.setSessionId);
            return;
        };
        
        // Window methods
        if (data.alert) {
            window.alert(data.alert);
            return;
        };

        if (data.open) {
            if (data.open.new_page) {
                window.open(data.open.path, '_blank');
            } else {
                window.location.href = data.open.path;
            }
            return;
        };

        if (data.confirm) {
            const result = window.confirm(data.confirm);
            socket.send(
                JSON.stringify(getEventData({window_response: { confirm_result: result, confirm_id: data.confirm_id }}))
            );
            return;
        };

        if (data.prompt) {
            const result = window.prompt(data.prompt.message, data.prompt.default || "");
            socket.send(
                JSON.stringify(getEventData({window_response: { prompt_result: result, prompt_id: data.prompt_id }}))
            );
            return;
        };

        if (data.close) {
            window.close();
            return;
        };

        if (data.scroll_to) {
            window.scrollTo({left: data.scroll_to.x, top: data.scroll_to.y, behavior: data.scroll_to.behavior});
            return;
        };

        if (data.scroll_by) {
            window.scrollBy({left: data.scroll_by.x, top: data.scroll_by.y, behavior: data.scroll_by.behavior});
            return;
        };

        if (data.set_timeout) {
            const timerId = setTimeout(() => {
                // Notificar o Python que o timeout foi concluído
                socket.send(
                    JSON.stringify(getEventData({window_response: { timeout_completed: true, timeout_id: data.set_timeout.id }}))
                );
            }, data.set_timeout.delay);
            
            // Armazenar o ID do timer para poder cancelá-lo mais tarde
            window.pyTimers = window.pyTimers || {};
            window.pyTimers[data.set_timeout.id] = timerId;
            return;
        };

        if (data.set_interval) {
            const intervalId = setInterval(() => {
                // Notificar o Python que o intervalo foi executado
                socket.send(
                    JSON.stringify(getEventData({window_response: { interval_executed: true, interval_id: data.set_interval.id }}))
                );
            }, data.set_interval.interval);
            
            // Armazenar o ID do intervalo para poder cancelá-lo mais tarde
            window.pyIntervals = window.pyIntervals || {};
            window.pyIntervals[data.set_interval.id] = intervalId;
            return;
        };

        if (data.clear_timeout) {
            if (window.pyTimers && window.pyTimers[data.clear_timeout.id]) {
                clearTimeout(window.pyTimers[data.clear_timeout.id]);
                delete window.pyTimers[data.clear_timeout.id];
            }
            return;
        };


        if (data.clear_interval) {
            if (window.pyIntervals && window.pyIntervals[data.clear_interval.id]) {
                clearInterval(window.pyIntervals[data.clear_interval.id]);
                delete window.pyIntervals[data.clear_interval.id];
            }
            return;
        };

        // request_animation_frame
        if (data.request_animation_frame) {
            const frameId = requestAnimationFrame(() => {
                // Notificar o Python que o frame foi processado
                socket.send(
                    JSON.stringify(getEventData({window_response: { animation_frame_executed: true, frame_id: data.request_animation_frame.id }}))
                );
            });
            
            // Armazenar o ID do frame para poder cancelá-lo mais tarde
            window.pyAnimationFrames = window.pyAnimationFrames || {};
            window.pyAnimationFrames[data.request_animation_frame.id] = frameId;
            return;
        };
        
        // cancel_animation_frame
        if (data.cancel_animation_frame) {
            if (window.pyAnimationFrames && window.pyAnimationFrames[data.cancel_animation_frame.id]) {
                cancelAnimationFrame(window.pyAnimationFrames[data.cancel_animation_frame.id]);
                delete window.pyAnimationFrames[data.cancel_animation_frame.id];
            }
            return;
        };

        if (data.localstorage) {
            const values = Object.entries(data.localstorage);
            localStorage.clear();

            values.forEach(([key, value]) => {
                localStorage.setItem(key, value);
            })
        };

        if (data.sessionstorage) {
            const values = Object.entries(data.sessionstorage);
            const sessionId = getsessionId();
            sessionStorage.clear();
            
            values.forEach(([key, value]) => {
                if (key !== '_pyweber_sessionId') {
                    sessionStorage.setItem(key, value);
                } else {
                    sessionStorage.setItem(key, sessionId);
                };
            })
        };

        
        if (data.Error) {
            console.log(data)
        };

    };

    return socket
}

function applyDifferences(differences) {
    Object.keys(differences).forEach(key => {
        const diff = differences[key];
        
        // Se não tem parent, só pode ser uma mudança no elemento raiz
        if (!diff.parent) {
            if (diff.status === 'Changed') {
                const parser = new DOMParser();
                const doc = parser.parseFromString(diff.element, 'text/html');
                document.documentElement.innerHTML = doc.documentElement.innerHTML;
            }
            return;
        }
        
        // Para elementos com parent
        const parentElement = document.querySelector(`[uuid="${diff.parent}"]`);
        if (!parentElement) return;
        
        switch(diff.status) {
            case 'Added':
                const temp = createElementFromHTML(diff.element);
                parentElement.appendChild(temp);
                break;
                
            case 'Removed':
                const toRemove = parentElement.querySelector(`[uuid="${diff.element}"]`);
                if (toRemove) toRemove.remove();
                break;
                
            case 'Changed':
                let uuid;
                if (typeof diff.element === 'string' && diff.element.startsWith('<')) {
                    const match = diff.element.match(/uuid=['"]([^'"]+)['"]/);
                    uuid = match ? match[1] : null;
                } else {
                    uuid = diff.element;
                }
                
                if (uuid) {
                    const toChange = parentElement.querySelector(`[uuid="${uuid}"]`);
                    if (toChange) {
                        const temp = createElementFromHTML(diff.element);
                        toChange.parentNode.replaceChild(temp, toChange);
                    }
                }
                break;
        }
    });
}

function createElementFromHTML(html) {
    const containerMap = {
        tr: ['table', 'tbody'],
        td: ['table', 'tbody', 'tr'],
        th: ['table', 'tbody', 'tr'],
        li: ['ul'],
        option: ['select'],
    };

    const match = html.trim().match(/^<([a-z0-9-]+)/i);
    const tag = match ? match[1].toLowerCase() : null;

    let container = document.createElement('div');

    if (tag in containerMap) {
        for (const tagName of containerMap[tag]) {
            const el = document.createElement(tagName);
            container.appendChild(el);
            container = el;
        }
    }

    container.innerHTML = html;
    return container.firstElementChild;
}


function getsessionId() {
    return sessionStorage.getItem('_pyweber_sessionId') || null;
}

function setSessionId(sessionId) {
    if (!getsessionId()) {
        sessionStorage.setItem('_pyweber_sessionId', sessionId);
    }
}

function sendEvent({type, event, event_ref, window_response}) {

    if (event_ref === EventRef.WINDOW && !window_event_received) {
        earyEventsBuffer.push({type, event, event_ref, window_response});
        return;
    };

    const target = event.target instanceof HTMLElement ? event.target : null;
    const eventData = getEventData({type, event, event_ref, window_response});

    if (socket.readyState === WebSocket.OPEN) {
        if (target && event_ref == EventRef.DOCUMENT) {
            if (target.getAttribute(`_on${type}`)) {
                socket.send(JSON.stringify(eventData));
            };
        };

        if (event_ref === EventRef.WINDOW) {
            if (sessionStorage.getItem(type)) {
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

function getEventData({type=null, event=null, event_ref=null, window_response=null}) {
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
        window_response: window_response ? window_response : {},
        window_event: event_ref === EventRef.WINDOW ? sessionStorage.getItem(type): null,
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
            if (input.type === 'radio') {
                if (input.checked) {
                    input.setAttribute('checked', '');
                    values[id] = input.value;
                } else {
                    input.removeAttribute('checked');
                }
            } else if (input.type === 'checkbox') {
                if (input.checked) {
                    values[id] = input.value;
                    input.setAttribute('checked', '');
                } else {
                    input.removeAttribute('checked');
                };
                
            } else if (input.tagName === 'SELECT') {
                values[id] = input.value;

                const options = input.querySelectorAll('option');
                options.forEach(option => {
                    if (option.value === input.value) {
                        option.setAttribute('selected', '');
                        values[id] = option.value;
                    } else {
                        option.removeAttribute('selected');
                    }
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