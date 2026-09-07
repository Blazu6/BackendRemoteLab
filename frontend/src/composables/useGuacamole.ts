import { ref, onUnmounted } from 'vue';
import Guacamole from 'guacamole-common-js';

export interface ConnectionConfig {
    id?: number;
    name?: string;
    protocol: string;
    hostname: string;
    port: string;
    username?: string;
    password?: string;
    shadow?: 'readonly' | 'interactive' | boolean;
    is_active?: boolean;
}

export function useGuacamole() {
    const isConnected = ref(false);
    const connectionState = ref<number>(0);
    const errorMessage = ref<string | null>(null);

    let client: Guacamole.Client | null = null;
    let tunnel: Guacamole.WebSocketTunnel | null = null;
    let keyboard: Guacamole.Keyboard | null = null;
    let mouse: Guacamole.Mouse | null = null;
    let rescaleFn: (() => void) | null = null;
    let syncLocalClipboardToRemote: (() => Promise<void>) | null = null;
    
    // ZMIANA 1: Dodajemy zmienną do obsługi opóźnienia wysyłania rozdzielczości (Debounce)
    let resizeTimeout: ReturnType<typeof setTimeout> | null = null;

    const disconnect = () => {
        // Czyszczenie opóźnionego rozmiaru
        if (resizeTimeout) {
            clearTimeout(resizeTimeout);
            resizeTimeout = null;
        }

        if (keyboard) {
            keyboard.onkeydown = null;
            keyboard.onkeyup = null;
            keyboard = null;
        }

        if (mouse) {
            mouse.onmousedown = null;
            mouse.onmouseup = null;
            mouse.onmousemove = null;
            mouse = null;
        }

        if (client) {
            if (rescaleFn) {
                window.removeEventListener('resize', rescaleFn);
                rescaleFn = null;
            }
            if (syncLocalClipboardToRemote) {
                window.removeEventListener('focus', syncLocalClipboardToRemote);
                syncLocalClipboardToRemote = null;
            }
            client.disconnect();
            client = null;
        }

        tunnel = null;
        isConnected.value = false;
    };

    const connect = (displayContainer: HTMLElement, config: ConnectionConfig) => {
        disconnect();
        errorMessage.value = null;

        const shadowParam = config.shadow === true ? 'interactive' : (config.shadow || undefined);
        const queryParams = new URLSearchParams({
            machine_id: config.id ? config.id.toString() : '',
            width: displayContainer.clientWidth.toString(),
            height: displayContainer.clientHeight.toString(),
            ...(shadowParam ? { shadow: shadowParam } : {})
        }).toString();

        const wsUrl = `ws://${window.location.host}/ws/guacamole/`;
        tunnel = new Guacamole.WebSocketTunnel(wsUrl);
        client = new Guacamole.Client(tunnel);

        const display = client.getDisplay();
        const displayElement = display.getElement();
        displayContainer.innerHTML = '';
        displayContainer.appendChild(displayElement);

        const rescale = () => {
            if (!client) return;
            const containerWidth = displayContainer.clientWidth;
            const containerHeight = displayContainer.clientHeight;
            
            if (containerWidth < 300 || containerHeight < 200) return;
            
            const displayWidth = display.getWidth();
            const displayHeight = display.getHeight();
            
            if (displayWidth > 0 && displayHeight > 0) {
                const scale = Math.min(
                    containerWidth / displayWidth,
                    containerHeight / displayHeight
                );
                
                // Niezależnie od opóźnień, UI skalujemy błyskawicznie
                display.scale(scale);

                const scaledWidth = displayWidth * scale;
                const scaledHeight = displayHeight * scale;
                displayElement.style.marginLeft = `${(containerWidth - scaledWidth) / 2}px`;
                displayElement.style.marginTop = `${(containerHeight - scaledHeight) / 2}px`;
            }

            // ZMIANA 2: Zabezpieczenie przed atakiem "resize". 
            // Czekamy 400ms od ostatniego ruchu okna przeglądarki, zanim wyślemy komendę do serwera.
            if (resizeTimeout) clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (client && isConnected.value) {
                    (client as any).sendSize(containerWidth, containerHeight);
                }
            }, 400);
        };

        display.onresize = (_width: number, _height: number) => {
            rescale();
        };

        window.addEventListener('resize', rescale);
        rescaleFn = rescale;

        if (config.shadow !== 'readonly') {
            displayContainer.setAttribute('tabindex', '0');
            displayContainer.style.outline = 'none';

            keyboard = new Guacamole.Keyboard(displayContainer);
            keyboard.onkeydown = (keysym: number) => {
                if (client && isConnected.value) client.sendKeyEvent(1, keysym);
            };
            keyboard.onkeyup = (keysym: number) => {
                if (client && isConnected.value) client.sendKeyEvent(0, keysym);
            };

            mouse = new Guacamole.Mouse(displayElement);
            mouse.onmousedown = mouse.onmouseup = mouse.onmousemove = (mouseState: Guacamole.Mouse.State) => {
                if (client && isConnected.value) {
                    // ZMIANA 3: Naprawa uciekającej myszki! 
                    // Pobieramy aktualną skalę obrazu i dzielimy przez nią współrzędne systemowe.
                    const currentScale = (display as any).getScale();
                    const scaledMouseState = {
                        ...mouseState,
                        x: mouseState.x / currentScale,
                        y: mouseState.y / currentScale
                    };
                    
                    client.sendMouseState(scaledMouseState as Guacamole.Mouse.State);
                }
            };

            displayElement.style.cursor = 'none';
        } else {
            displayElement.style.cursor = 'default';
        }

        (client as any).onclipboard = (stream: any, mimetype: string) => {
            if (mimetype === 'text/plain') {
                const reader = new (Guacamole as any).StringReader(stream);
                let data = '';
                reader.ontext = (text: string) => { data += text; };
                reader.onend = () => {
                    if (navigator.clipboard) {
                        navigator.clipboard.writeText(data).catch(err => {
                            console.warn('Nie można zapisać do lokalnego schowka:', err);
                        });
                    }
                };
            }
        };

        syncLocalClipboardToRemote = async () => {
            if (!client || !isConnected.value || !navigator.clipboard) return;
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    const stream = (client as any).createClipboardStream('text/plain');
                    const writer = new (Guacamole as any).StringWriter(stream);
                    writer.sendText(text);
                    writer.sendEnd();
                }
            } catch (err) {
                console.warn('Nie można odczytać lokalnego schowka:', err);
            }
        };

        window.addEventListener('focus', syncLocalClipboardToRemote);
        displayContainer.addEventListener('mouseenter', syncLocalClipboardToRemote);

        client.onstatechange = (state: number) => {
            console.log('🔄 Stan klienta Guacamole:', state);
            connectionState.value = state;
            isConnected.value = state === 3;

            if (state === 3) {
                setTimeout(() => rescale(), 150);
            }
        };

        client.onerror = (error: { message?: string }) => {
            console.error('❌ Błąd klienta Guacamole:', error);
            errorMessage.value = error.message || 'Wystąpił błąd podczas połączenia.';
            isConnected.value = false;
        };

        client.connect(queryParams);
    };

    onUnmounted(() => {
        disconnect();
    });

    const triggerRescale = () => {
        if (rescaleFn) rescaleFn();
    };

    return {
        isConnected,
        connectionState,
        errorMessage,
        connect,
        disconnect,
        triggerRescale,
    };
}