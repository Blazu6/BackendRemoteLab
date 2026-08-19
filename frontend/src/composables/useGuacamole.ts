import { ref, onUnmounted } from 'vue';
import Guacamole from 'guacamole-common-js';

export interface ConnectionConfig {
    id?: number; // Opcjonalne przed zapisem
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
    let isKeyboardEnabled = true;

    /**
     * Zwalnia zasoby, usuwa nasłuchiwacze i zamyka połączenie
     */
    const disconnect = () => {
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

    /**
     * Nawiązuje połączenie WebSocket z Django i inicjalizuje Guacamole
     */
    const connect = (displayContainer: HTMLElement, config: ConnectionConfig) => {
        // 1. Rozłączamy ewentualne poprzednie połączenie i resetujemy błędy
        disconnect();
        errorMessage.value = null;

        // 2. Budujemy parametry zapytania (tylko ID maszyny i rozmiar)
        const shadowParam = config.shadow === true ? 'interactive' : (config.shadow || undefined);
        const queryParams = new URLSearchParams({
            machine_id: config.id ? config.id.toString() : '',
            width: displayContainer.clientWidth.toString(),
            height: displayContainer.clientHeight.toString(),
            ...(shadowParam ? { shadow: shadowParam } : {})
        }).toString();

        // 3. Utworzenie tunelu WebSocket oraz Klienta Guacamole
        const wsUrl = `ws://${window.location.host}/ws/guacamole/`;
        tunnel = new Guacamole.WebSocketTunnel(wsUrl);
        client = new Guacamole.Client(tunnel);

        // 4. Podpięcie elementu wyjściowego (Canvas) do kontenera w HTML
        const display = client.getDisplay();

        const displayElement = display.getElement();
        displayContainer.innerHTML = '';
        displayContainer.appendChild(displayElement);

        // 4a. Auto-skalowanie display'a do rozmiaru kontenera (ważne dla VNC/RDP)
        const rescale = () => {
            if (!client) return;
            const containerWidth = displayContainer.clientWidth;
            const containerHeight = displayContainer.clientHeight;
            // Pomijaj skalowanie gdy kontener jest za mały (np. zminimalizowany)
            if (containerWidth < 300 || containerHeight < 200) return;
            const displayWidth = display.getWidth();
            const displayHeight = display.getHeight();
            if (displayWidth > 0 && displayHeight > 0) {
                const scale = Math.min(
                    containerWidth / displayWidth,
                    containerHeight / displayHeight
                );
                display.scale(scale);

                // Ręczne centrowanie elementu (zamiast flexboxa, który psuł transform-origin: 0 0)
                const scaledWidth = displayWidth * scale;
                const scaledHeight = displayHeight * scale;
                displayElement.style.marginLeft = `${(containerWidth - scaledWidth) / 2}px`;
                displayElement.style.marginTop = `${(containerHeight - scaledHeight) / 2}px`;
            }

            // Wysłanie nowej rozdzielczości do serwera zdalnego (wymusza np. zmianę kolumn/wierszy w SSH)
            if (isConnected.value) {
                (client as any).sendSize(containerWidth, containerHeight);
            }
        };

        display.onresize = (_width: number, _height: number) => {
            rescale();
        };

        window.addEventListener('resize', rescale);
        rescaleFn = rescale;

        // 5. Inicjalizacja klawiatury i myszy (Tylko jeśli to nie jest tryb read-only!)
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
                    client.sendMouseState(mouseState);
                }
            };

            // Przywrócono na życzenie: ukrywamy sprzętowy kursor
            displayElement.style.cursor = 'none';
        } else {
            // W trybie podglądu pokazujemy zwykły kursor
            displayElement.style.cursor = 'default';
        }

        // 7. Obsługa schowka (Remote -> Local)
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

        // 8. Obsługa schowka (Local -> Remote)
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
                console.warn('Nie można odczytać lokalnego schowka (może brak uprawnień):', err);
            }
        };

        window.addEventListener('focus', syncLocalClipboardToRemote);
        // Synchronizacja przy kliknięciu/wejściu w obszar terminala dla pewności
        displayContainer.addEventListener('mouseenter', syncLocalClipboardToRemote);

        // 9. Obsługa zmian stanu połączenia
        client.onstatechange = (state: number) => {
            console.log('🔄 Stan klienta Guacamole:', state);
            connectionState.value = state;
            // Stan 3 odpowiada wartości CONNECTED w Guacamole.Client
            isConnected.value = state === 3;

            // Wymuszenie skalowania gdy element staje się widoczny (v-show)
            if (state === 3) {
                // setTimeout daje czas na nałożenie v-show przez Vue i wyliczenie rozmiarów (zwiększone z 50 do 150)
                setTimeout(() => triggerRescale(), 150);
            }
        };

        client.onerror = (error: { message?: string }) => {
            console.error('❌ Błąd klienta Guacamole:', error);
            errorMessage.value = error.message || 'Wystąpił błąd podczas połączenia.';
            isConnected.value = false;
        };

        // 10. Rozpoczęcie procesu łączenia (query trafia jako ?query do URL tunelu)
        client.connect(queryParams);
    };

    // Automatyczne sprzątanie w przypadku opuszczenia widoku przez użytkownika
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