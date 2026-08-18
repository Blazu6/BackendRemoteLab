import { ref, onUnmounted } from 'vue';
import Guacamole from 'guacamole-common-js';

export interface ConnectionConfig {
    protocol: string;
    hostname: string;
    port: string;
    username: string;
    password?: string;
}

export function useGuacamole() {
    const isConnected = ref(false);
    const connectionState = ref<number>(0);
    const errorMessage = ref<string | null>(null);

    let client: Guacamole.Client | null = null;
    let tunnel: Guacamole.WebSocketTunnel | null = null;
    let keyboard: Guacamole.Keyboard | null = null;
    let mouse: Guacamole.Mouse | null = null;

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
            if ((client as any).__rescaleCleanup) {
                (client as any).__rescaleCleanup();
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

        // 2. Budujemy parametry zapytania
        const queryParams = new URLSearchParams({
            protocol: config.protocol,
            hostname: config.hostname,
            port: config.port,
            username: config.username,
            password: config.password || '',
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
            const displayWidth = display.getWidth();
            if (displayWidth > 0 && containerWidth > 0) {
                const scale = Math.min(containerWidth / displayWidth, 1);
                display.scale(scale);
            }
        };

        display.onresize = (_width: number, _height: number) => {
            rescale();
        };

        window.addEventListener('resize', rescale);
        // Zapisujemy referencję do cleanup w disconnect
        (client as any).__rescaleCleanup = () => window.removeEventListener('resize', rescale);

        // 5. Inicjalizacja klawiatury (globalnie)
        keyboard = new Guacamole.Keyboard(document);
        keyboard.onkeydown = (keysym: number) => {
            if (client && isConnected.value) {
                client.sendKeyEvent(1, keysym);
            }
        };
        keyboard.onkeyup = (keysym: number) => {
            if (client && isConnected.value) {
                client.sendKeyEvent(0, keysym);
            }
        };

        // 6. Inicjalizacja myszy (na elemencie terminala)
        mouse = new Guacamole.Mouse(displayElement);
        mouse.onmousedown = mouse.onmouseup = mouse.onmousemove = (mouseState: Guacamole.Mouse.State) => {
            if (client && isConnected.value) {
                client.sendMouseState(mouseState);
            }
        };

        // 7. Obsługa zmian stanu połączenia
        client.onstatechange = (state: number) => {
            console.log('🔄 Stan klienta Guacamole:', state);
            connectionState.value = state;
            // Stan 3 odpowiada wartości CONNECTED w Guacamole.Client
            isConnected.value = state === 3;
        };

        client.onerror = (error: { message?: string }) => {
            console.error('❌ Błąd klienta Guacamole:', error);
            errorMessage.value = error.message || 'Wystąpił błąd podczas połączenia.';
            isConnected.value = false;
        };

        // 8. Rozpoczęcie procesu łączenia (query trafia jako ?query do URL tunelu)
        client.connect(queryParams);
    };

    // Automatyczne sprzątanie w przypadku opuszczenia widoku przez użytkownika
    onUnmounted(() => {
        disconnect();
    });

    return {
        isConnected,
        connectionState,
        errorMessage,
        connect,
        disconnect,
    };
}