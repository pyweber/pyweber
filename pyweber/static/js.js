let socket;
let socketReady = false;
let window_event_received = false;
const earlyEventsBuffer = [];
const activeListeners = [];
const fileMap = {};
const fileSignatureMap = {};

let reconnectAttempts = 0;
const maxReconnectAttempts = 2;

const EventRef = new Proxy(
    { DOCUMENT: 'document', WINDOW: 'window' },
    {
        set(target, prop, value) {
            throw new Error(`Cannot modify constant ${prop}`);
        }
    }
);

// ─── Compressão + envio centralizado ─────────────────────────────────────────
async function compress(data) {
    const json = typeof data === 'string' ? data : JSON.stringify(data);
    const stream = new CompressionStream('gzip');
    const writer = stream.writable.getWriter();
    writer.write(new TextEncoder().encode(json));
    writer.close();
    return new Uint8Array(await new Response(stream.readable).arrayBuffer());
}

async function sendToServer(data) {
    if (socket.readyState !== WebSocket.OPEN) return;
    socket.send(await compress(data));
}

// ─── WebSocket ────────────────────────────────────────────────────────────────
function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(`${wsProtocol}//${window.location.host}`);

    socket.onopen = async function () {
        socketReady = true;
        reconnectAttempts = 0;
        sendToServer(await getEventData({}));
    };

    socket.onerror = function (error) {
        console.error('Erro com a ligação WebSocket:', error);
    };

    socket.onclose = function () {
        socketReady = false;
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`WebSocket fechado. Nova tentativa em 1s... (${reconnectAttempts}/${maxReconnectAttempts})`);
            setTimeout(connectWebSocket, 1000);
        } else {
            console.warn('Número máximo de tentativas de reconexão atingido.');
        }
    };

    socket.onmessage = async function (event) {
        // Suporta resposta do servidor em bytes ou string
        const raw = event.data instanceof ArrayBuffer
            ? new TextDecoder().decode(event.data)
            : (event.data instanceof Blob
                ? new TextDecoder().decode(await event.data.arrayBuffer())
                : event.data);

        const data = JSON.parse(raw);

        if (data.windowEvents) {
            Object.keys(sessionStorage).forEach(item => {
                if (item !== '_pyweber_sessionId') sessionStorage.removeItem(item);
            });

            for (const eventName of data.windowEvents) {
                const palavra = eventName.replace(/^_on/, '');
                const evt = palavra.split('_')[0];
                sessionStorage.setItem(evt, eventName);
            }

            if (!window_event_received) {
                window_event_received = true;
                earlyEventsBuffer.forEach(item => sendEvent(item));
                earlyEventsBuffer.length = 0;
            }
            return;
        }

        if (data.request_file) {
            const response = await get_file_content(data.request_file, data.start, data.end);
            await send_file_chunk(response.file_id, response.status, response.data);
            return;
        }

        if (data.template) {
            applyDifferences(data.template);
            return;
        }

        if (data.reload) {
            location.reload();
            return;
        }

        if (data.setSessionId) {
            setSessionId(data.setSessionId);
            return;
        }

        // ── Métodos de janela ──────────────────────────────────────────────────

        if (data.alert) {
            window.alert(data.alert);
            return;
        }

        if (data.open) {
            data.open.new_page
                ? window.open(data.open.path, '_blank')
                : (window.location.href = data.open.path);
            return;
        }

        if (data.confirm) {
            const result = window.confirm(data.confirm);
            sendToServer(await getEventData({
                window_response: { confirm_result: result, confirm_id: data.confirm_id }
            }));
            return;
        }

        if (data.prompt) {
            const result = window.prompt(data.prompt.message, data.prompt.default || '');
            sendToServer(await getEventData({
                window_response: { prompt_result: result, prompt_id: data.prompt_id }
            }));
            return;
        }

        if (data.close) {
            window.close();
            return;
        }

        if (data.scroll_to) {
            window.scrollTo({ left: data.scroll_to.x, top: data.scroll_to.y, behavior: data.scroll_to.behavior });
            return;
        }

        if (data.scroll_by) {
            window.scrollBy({ left: data.scroll_by.x, top: data.scroll_by.y, behavior: data.scroll_by.behavior });
            return;
        }

        if (data.set_timeout) {
            window.pyTimers = window.pyTimers || {};
            window.pyTimers[data.set_timeout.id] = setTimeout(async () => {
                sendToServer(await getEventData({
                    window_response: { timeout_completed: true, timeout_id: data.set_timeout.id }
                }));
            }, data.set_timeout.delay);
            return;
        }

        if (data.set_interval) {
            window.pyIntervals = window.pyIntervals || {};
            window.pyIntervals[data.set_interval.id] = setInterval(async () => {
                sendToServer(await getEventData({
                    window_response: { interval_executed: true, interval_id: data.set_interval.id }
                }));
            }, data.set_interval.interval);
            return;
        }

        if (data.clear_timeout) {
            if (window.pyTimers?.[data.clear_timeout.id]) {
                clearTimeout(window.pyTimers[data.clear_timeout.id]);
                delete window.pyTimers[data.clear_timeout.id];
            }
            return;
        }

        if (data.clear_interval) {
            if (window.pyIntervals?.[data.clear_interval.id]) {
                clearInterval(window.pyIntervals[data.clear_interval.id]);
                delete window.pyIntervals[data.clear_interval.id];
            }
            return;
        }

        if (data.request_animation_frame) {
            window.pyAnimationFrames = window.pyAnimationFrames || {};
            window.pyAnimationFrames[data.request_animation_frame.id] = requestAnimationFrame(async () => {
                sendToServer(await getEventData({
                    window_response: {
                        animation_frame_executed: true,
                        frame_id: data.request_animation_frame.id
                    }
                }));
            });
            return;
        }

        if (data.cancel_animation_frame) {
            if (window.pyAnimationFrames?.[data.cancel_animation_frame.id]) {
                cancelAnimationFrame(window.pyAnimationFrames[data.cancel_animation_frame.id]);
                delete window.pyAnimationFrames[data.cancel_animation_frame.id];
            }
            return;
        }

        if (data.localstorage) {
            localStorage.clear();
            Object.entries(data.localstorage).forEach(([key, value]) => localStorage.setItem(key, value));
        }

        if (data.sessionstorage) {
            const sessionId = getsessionId();
            sessionStorage.clear();
            Object.entries(data.sessionstorage).forEach(([key, value]) => {
                sessionStorage.setItem(key, key === '_pyweber_sessionId' ? sessionId : value);
            });
        }

        if (data.Error) {
            console.error('[PyWeber Error]', data);
        }
    };

    return socket;
}

// ─── Envio de ficheiro via HTTP (mantém binário puro, sem compressão JSON) ────
async function send_file_chunk(file_id, status, data) {
    await fetch(`/_pyweber/file_chunk?file_id=${file_id}&status=${status}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream' },
        body: data instanceof ArrayBuffer ? data : new TextEncoder().encode(data)
    });
}

// ─── DOM ──────────────────────────────────────────────────────────────────────
function applyDifferences(differences) {
    Object.keys(differences).forEach(key => {
        const diff = differences[key];

        if (!diff.parent) {
            if (diff.status === 'Changed') {
                const doc = new DOMParser().parseFromString(diff.element, 'text/html');
                document.documentElement.innerHTML = doc.documentElement.innerHTML;
            }
            return;
        }

        const parentElement = document.querySelector(`[uuid="${diff.parent}"]`);
        if (!parentElement) return;

        switch (diff.status) {
            case 'Added':
                parentElement.appendChild(createElementFromHTML(diff.element));
                break;

            case 'Removed': {
                const toRemove = parentElement.querySelector(`[uuid="${diff.element}"]`);
                toRemove?.remove();
                break;
            }

            case 'Changed': {
                const uuid = typeof diff.element === 'string' && diff.element.startsWith('<')
                    ? (diff.element.match(/uuid=['"]([^'"]+)['"]/) || [])[1] ?? null
                    : diff.element;

                if (uuid) {
                    const toChange = parentElement.querySelector(`[uuid="${uuid}"]`);
                    if (toChange) {
                        toChange.parentNode.replaceChild(createElementFromHTML(diff.element), toChange);
                    }
                }
                break;
            }
        }

        if (diff.methods) {
            const target_element = parentElement.querySelector(`[uuid="${key}"]`);
            execute_event_handlers(target_element, diff.methods);
        }
    });
}

function execute_event_handlers(element, methods) {
    if (!(element instanceof HTMLElement)) return;
    Object.entries(methods).forEach(([method, params]) => {
        if (typeof element[method] === 'function') {
            element[method](...Object.values(params));
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

    if (tag && tag in containerMap) {
        for (const tagName of containerMap[tag]) {
            const el = document.createElement(tagName);
            container.appendChild(el);
            container = el;
        }
    }

    container.innerHTML = html;
    return container.firstElementChild;
}

// ─── Sessão ───────────────────────────────────────────────────────────────────
function getsessionId() {
    return sessionStorage.getItem('_pyweber_sessionId') || null;
}

function setSessionId(sessionId) {
    if (!getsessionId()) {
        sessionStorage.setItem('_pyweber_sessionId', sessionId);
    }
}

// ─── Envio de eventos ─────────────────────────────────────────────────────────
async function sendEvent({ type, event, event_ref, window_response }) {
    if (event_ref === EventRef.WINDOW && !window_event_received) {
        earlyEventsBuffer.push({ type, event, event_ref, window_response });
        return;
    }

    const eventData = await getEventData({ type, event, event_ref, window_response });

    if (socket.readyState !== WebSocket.OPEN) return;

    if (event_ref === EventRef.DOCUMENT && eventData.current_target_uuid) {
        sendToServer(eventData);
    } else if (event_ref === EventRef.WINDOW && sessionStorage.getItem(type)) {
        sendToServer(eventData);
    }
}

// ─── Utilitários Base64 ───────────────────────────────────────────────────────
function toBase64(string) {
    const encoded = new TextEncoder().encode(string);
    let binary = '';
    encoded.forEach(byte => (binary += String.fromCharCode(byte)));
    return btoa(binary);
}

function fromBase64(base64) {
    return new TextDecoder().decode(Uint8Array.from(atob(base64), c => c.charCodeAt(0)));
}

// ─── Construção do payload ────────────────────────────────────────────────────
async function getEventData({ type = null, event = null, event_ref = null, window_response = null, file_content = null }) {
    const target = event?.target instanceof HTMLElement ? event.target : null;
    const values = await getFormValues();

    return {
        type,
        event_ref,
        route: window.location.pathname,
        target_uuid: target?.getAttribute('uuid') ?? null,
        current_target_uuid: target?.closest(`[_on${type}]`)?.getAttribute('uuid') ?? null,
        template: document.documentElement.outerHTML,
        values,                         // ← sem JSON.stringify desnecessário
        event_data: {
            clientX: event?.clientX ?? null,
            clientY: event?.clientY ?? null,
            screenX: event?.screenX ?? null,
            screenY: event?.screenY ?? null,
            pageX: event?.pageX ?? null,
            pageY: event?.pageY ?? null,
            button: event?.button ?? null,
            buttons: event?.buttons ?? null,
            key: event?.key ?? null,
            code: event?.code ?? null,
            keyCode: event?.keyCode ?? null,
            ctrlKey: event?.ctrlKey ?? false,
            shiftKey: event?.shiftKey ?? false,
            altKey: event?.altKey ?? false,
            metaKey: event?.metaKey ?? false,
            repeat: event?.repeat ?? false,
            deltaX: event?.deltaX ?? null,
            deltaY: event?.deltaY ?? null,
            deltaZ: event?.deltaZ ?? null,
            deltaMode: event?.deltaMode ?? null,
            touches: event?.touches?.length ?? null,
            changedTouches: event?.changedTouches?.length ?? null,
            targetTouches: event?.targetTouches?.length ?? null,
            dataTransfer: event?.dataTransfer ? {
                dropEffect: event.dataTransfer.dropEffect,
                effectAllowed: event.dataTransfer.effectAllowed,
                files: event.dataTransfer.files?.length ?? 0,
                types: Array.from(event.dataTransfer.types ?? [])
            } : null,
            clipboardData: event?.clipboardData ? {
                types: Array.from(event.clipboardData.types ?? []),
                text: event.clipboardData.getData?.('text/plain') ?? null
            } : null,
            animationName: event?.animationName ?? null,
            elapsedTime: event?.elapsedTime ?? null,
            propertyName: event?.propertyName ?? null,
            pseudoElement: event?.pseudoElement ?? null,
            isTrusted: event?.isTrusted ?? null,
            bubbles: event?.bubbles ?? null,
            cancelable: event?.cancelable ?? null,
            defaultPrevented: event?.defaultPrevented ?? false,
            eventPhase: event?.eventPhase ?? null,
            timestamp: Date.now()
        },
        window_data: getWindowData(),   // ← sem JSON.stringify desnecessário
        window_response: window_response ?? {},
        window_event: event_ref === EventRef.WINDOW ? sessionStorage.getItem(type) : null,
        file_content: file_content ?? {},
        sessionId: getsessionId()
    };
}

// ─── Dados da janela ──────────────────────────────────────────────────────────
function getWindowData() {
    return {
        width: window.outerWidth,
        height: window.outerHeight,
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
        scrollX: window.scrollX,
        scrollY: window.scrollY,
        location: {
            href: window.location.href,
            protocol: window.location.protocol,
            host: window.location.host,
            port: window.location.port,
            pathname: window.location.pathname,
            origin: window.location.origin
        },
        localStorage: { ...localStorage },       // ← sem JSON.stringify
        sessionStorage: { ...sessionStorage },   // ← sem JSON.stringify
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
}

// ─── Leitura de ficheiros ─────────────────────────────────────────────────────
async function get_file_content(file_id, start, end) {
    const file = fileMap[file_id];

    if (!file) {
        return { file_id, status: 'error', data: 'File not found' };
    }

    const safeStart = Math.max(0, start);
    const safeEnd = end !== null ? Math.min(end, file.size) : file.size;

    if (safeStart >= file.size) {
        return { file_id, status: 'error', data: `Start index ${safeStart} exceeds file size ${file.size}` };
    }

    const buffer = await file.slice(safeStart, safeEnd).arrayBuffer();
    return { file_id, status: 'success', data: buffer };
}

function getOrCreateFileId(file) {
    for (const [id, existingFile] of Object.entries(fileMap)) {
        if (existingFile === file) return id;
    }

    const signature = `${file.name}_${file.size}_${file.lastModified}`;
    if (fileSignatureMap[signature]) return fileSignatureMap[signature];

    const file_id = crypto.randomUUID();
    fileMap[file_id] = file;
    fileSignatureMap[signature] = file_id;
    return file_id;
}

// ─── Valores de formulário ────────────────────────────────────────────────────
async function getFormValues() {
    const values = {};
    const inputs = document.querySelectorAll('input, textarea, select, option');

    for (const input of inputs) {
        const id = input.getAttribute('uuid');
        if (!id) continue;

        values[id] = {};

        if (input.type === 'radio') {
            if (input.checked) {
                input.setAttribute('checked', '');
                values[id].value = input.value;
            } else {
                input.removeAttribute('checked');
            }
        } else if (input.type === 'checkbox') {
            if (input.checked) {
                input.setAttribute('checked', '');
                values[id].value = input.value;
            } else {
                input.removeAttribute('checked');
            }
        } else if (input.type === 'file') {
            if (input.files) {
                values[id].value = Array.from(input.files).map(file => ({
                    size: file.size,
                    name: file.name,
                    file_id: getOrCreateFileId(file),
                    content_type: file.type || 'application/octet-stream',
                }));
            }
        } else if (input.tagName === 'SELECT') {
            input.querySelectorAll('option').forEach(option => {
                option.value === input.value
                    ? option.setAttribute('selected', '')
                    : option.removeAttribute('selected');
            });
            values[id].value = input.value;
        } else {
            values[id].value = input.value;
        }

        values[id].selection_start = input.selectionStart;
        values[id].selection_end = input.selectionEnd;
    }

    return values;
}

// ─── Rastreio de eventos ──────────────────────────────────────────────────────
function trackEvents() {
    const documentEvents = [
        'click', 'dblclick', 'mousedown', 'mouseup', 'mousemove', 'mouseover', 'mouseout',
        'mouseenter', 'mouseleave', 'contextmenu', 'wheel',
        'keydown', 'keyup', 'keypress',
        'focus', 'blur', 'change', 'input', 'submit', 'reset', 'select',
        'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop',
        'scroll', 'resize',
        'play', 'pause', 'ended', 'volumechange', 'seeked', 'seeking', 'timeupdate',
        'touchstart', 'touchmove', 'touchend', 'touchcancel'
    ];

    const windowEvents = [
        'afterprint', 'beforeprint', 'beforeunload', 'hashchange', 'load', 'pageshow', 'pagehide',
        'popstate', 'resize', 'scroll', 'DOMContentLoaded',
        'focus', 'blur', 'online', 'offline', 'storage',
        'message', 'messageerror',
        'error', 'abort', 'loadstart', 'progress', 'loadend', 'timeout',
        'animationstart', 'animationend', 'animationiteration',
        'transitionstart', 'transitionend', 'transitioncancel',
        'fullscreenchange', 'fullscreenerror', 'pointerlockchange', 'pointerlockerror',
        'devicemotion', 'deviceorientation', 'deviceorientationabsolute',
        'gamepadconnected', 'gamepaddisconnected',
        'install', 'activate', 'fetch', 'notificationclick', 'notificationclose',
        'push', 'pushsubscriptionchange', 'sync', 'periodicsync',
        'backgroundfetchsuccess', 'backgroundfetchfailure', 'backgroundfetchabort',
        'backgroundfetchclick', 'contentdelete',
        'cut', 'copy', 'paste',
        'select', 'selectionchange',
        'submit', 'reset', 'input', 'change', 'invalid', 'search', 'toggle', 'formdata',
        'play', 'pause', 'ended', 'volumechange', 'seeked', 'seeking', 'timeupdate',
        'canplay', 'canplaythrough', 'cuechange', 'durationchange', 'emptied',
        'loadeddata', 'loadedmetadata', 'stalled', 'suspend', 'waiting',
        'touchstart', 'touchend', 'touchmove', 'touchcancel',
        'pointerover', 'pointerenter', 'pointerdown', 'pointermove', 'pointerup',
        'pointercancel', 'pointerout', 'pointerleave', 'gotpointercapture', 'lostpointercapture',
        'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop',
        'keydown', 'keyup',
        'compositionstart', 'compositionupdate', 'compositionend',
        'visibilitychange',
        'rejectionhandled', 'unhandledrejection',
        'securitypolicyviolation'
    ];

    documentEvents.forEach(eventType => {
        document.addEventListener(eventType, event =>
            sendEvent({ type: eventType, event, event_ref: EventRef.DOCUMENT })
        );
    });

    windowEvents.forEach(eventType => {
        window.addEventListener(eventType, event =>
            sendEvent({ type: eventType, event, event_ref: EventRef.WINDOW })
        );
    });
}

// ─── Init ─────────────────────────────────────────────────────────────────────
connectWebSocket();
trackEvents();
