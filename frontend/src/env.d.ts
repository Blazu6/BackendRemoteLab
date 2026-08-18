/// <reference types="vite/client" />

declare module '*.vue' {
    import type { DefineComponent } from 'vue'
    const component: DefineComponent<{}, {}, any>
    export default component
}

declare module 'guacamole-common-js' {
    namespace Guacamole {
        class Client {
            constructor(tunnel: WebSocketTunnel);
            connect(data?: string): void;
            disconnect(): void;
            getDisplay(): Display;
            sendKeyEvent(pressed: 0 | 1, keysym: number): void;
            sendMouseState(state: Mouse.State): void;
            onstatechange: ((state: number) => void) | null;
            onerror: ((error: { message?: string }) => void) | null;
        }

        class Display {
            getElement(): HTMLElement;
        }

        class WebSocketTunnel {
            constructor(url: string);
        }

        class Keyboard {
            constructor(element: Document | HTMLElement);
            onkeydown: ((keysym: number) => void) | null;
            onkeyup: ((keysym: number) => void) | null;
        }

        namespace Mouse {
            interface State {
                x: number;
                y: number;
                left: boolean;
                middle: boolean;
                right: boolean;
            }
        }

        class Mouse {
            constructor(element: HTMLElement);
            onmousedown: ((state: Mouse.State) => void) | null;
            onmouseup: ((state: Mouse.State) => void) | null;
            onmousemove: ((state: Mouse.State) => void) | null;
        }
    }

    export default Guacamole;
}