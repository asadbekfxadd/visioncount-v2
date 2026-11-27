"use client";

import { useEffect, useRef } from "react";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

/**
 * Подключается к каналу VisionCount (/ws/dashboard или /ws/cameras/{id})
 * и вызывает onMessage для каждого ENTRY/EXIT события. Автоматически
 * переподключается при обрыве соединения.
 */
export function useWebSocket(path: string, onMessage: (data: any) => void) {
  const callbackRef = useRef(onMessage);
  callbackRef.current = onMessage;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;
    let closedByClient = false;

    function connect() {
      // WebSocket не умеет заголовки — JWT передаём параметром; без входа канал закрывается сервером
      const token = localStorage.getItem("vc_token") || "";
      socket = new WebSocket(`${WS_URL}${path}${path.includes("?") ? "&" : "?"}token=${encodeURIComponent(token)}`);

      socket.onmessage = (event) => {
        try {
          callbackRef.current(JSON.parse(event.data));
        } catch {
          /* ignore malformed frame */
        }
      };

      socket.onclose = () => {
        if (!closedByClient) {
          reconnectTimer = setTimeout(connect, 2000);
        }
      };

      socket.onerror = () => socket?.close();
    }

    connect();

    // Ping keep-alive every 20s so intermediary proxies don't drop the connection
    const ping = setInterval(() => {
      if (socket?.readyState === WebSocket.OPEN) socket.send("ping");
    }, 20000);

    return () => {
      closedByClient = true;
      clearTimeout(reconnectTimer);
      clearInterval(ping);
      socket?.close();
    };
  }, [path]);
}
