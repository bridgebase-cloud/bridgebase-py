"""Local TCP proxy that forwards traffic through the gateway socket.

App → Local Proxy (127.0.0.1:<ephemeral>) → Gateway Socket → Remote Gateway → DB

The proxy binds an ephemeral port on localhost.  DB clients connect to that
port; every accepted connection is forwarded byte‑for‑byte over the
persistent gateway control socket.

Phase‑1: single‑connection forwarding (one local‑port per DB client).
Phase‑3: connection multiplexing can be layered on top.
"""

from __future__ import annotations

import logging
import selectors
import socket
import struct
import threading
from typing import Optional

from bridgebase.exceptions import ProxyError

logger = logging.getLogger("bridgebase.proxy")

_CHUNK_SIZE = 65_536
# Frame header: 4‑byte big‑endian length prefix (max ~4 GiB per frame).
_LEN_FMT = "!I"
_LEN_SIZE = struct.calcsize(_LEN_FMT)


class ProxyManager:
    """Manages a local TCP listener that tunnels traffic through a gateway socket.

    Lifecycle
    ---------
    1. ``start(gateway_sock)`` — binds a local port, spawns a forwarding thread.
    2. ``local_port`` — the port DB clients should connect to.
    3. ``stop()`` — tears everything down.

    Thread‑safe: ``start`` / ``stop`` are guarded by a lock.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._listener: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._local_port: Optional[int] = None
        self._gateway_sock: Optional[socket.socket] = None

    # -- properties --------------------------------------------------------

    @property
    def local_port(self) -> int:
        """Port on 127.0.0.1 that the proxy is listening on."""
        if self._local_port is None:
            raise ProxyError("Proxy not started")
        return self._local_port

    @property
    def running(self) -> bool:
        return self._running

    # -- public ------------------------------------------------------------

    def start(self, gateway_sock: socket.socket) -> int:
        """Bind a local listener and begin forwarding.

        Returns the local port number that DB clients should connect to.
        """
        with self._lock:
            if self._running:
                assert self._local_port is not None
                return self._local_port

            self._gateway_sock = gateway_sock
            self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._listener.bind(("127.0.0.1", 0))
            self._listener.listen(1)
            self._listener.settimeout(1.0)  # allow periodic shutdown checks
            self._local_port = self._listener.getsockname()[1]

            self._running = True
            self._thread = threading.Thread(
                target=self._accept_loop,
                name="bridgebase-proxy",
                daemon=True,
            )
            self._thread.start()

            logger.debug("Proxy listening on 127.0.0.1:%d", self._local_port)
            return self._local_port

    def stop(self) -> None:
        """Stop the proxy and close all sockets."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        # Close the listener so the accept loop wakes up.
        if self._listener:
            try:
                self._listener.close()
            except OSError:
                pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        self._listener = None
        self._thread = None
        self._local_port = None
        logger.debug("Proxy stopped")

    # -- private -----------------------------------------------------------

    def _accept_loop(self) -> None:
        """Accept local connections and forward them through the gateway."""
        while self._running:
            try:
                assert self._listener is not None
                client_sock, addr = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                # Listener closed during shutdown.
                break

            logger.debug("Proxy accepted connection from %s", addr)
            # Each accepted connection gets its own forwarding pair.
            fwd = threading.Thread(
                target=self._forward,
                args=(client_sock,),
                name="bridgebase-proxy-fwd",
                daemon=True,
            )
            fwd.start()

    def _forward(self, client_sock: socket.socket) -> None:
        """Bidirectional forwarding between *client_sock* and the gateway socket.

        Uses a simple selector loop so both directions are handled in one
        thread without busy‑waiting.
        """
        gw = self._gateway_sock
        if gw is None:
            client_sock.close()
            return

        sel = selectors.DefaultSelector()
        try:
            client_sock.setblocking(False)
            gw.setblocking(False)
            sel.register(client_sock, selectors.EVENT_READ, data="client")
            sel.register(gw, selectors.EVENT_READ, data="gateway")

            while self._running:
                events = sel.select(timeout=1.0)
                for key, _ in events:
                    src: socket.socket = key.fileobj  # type: ignore[assignment]
                    dst = gw if key.data == "client" else client_sock
                    try:
                        data = src.recv(_CHUNK_SIZE)
                    except (BlockingIOError, InterruptedError):
                        continue
                    except OSError:
                        return
                    if not data:
                        return
                    try:
                        dst.sendall(data)
                    except OSError:
                        return
        except Exception:
            logger.debug("Proxy forwarding ended", exc_info=True)
        finally:
            sel.close()
            client_sock.close()
            # Don't close gw — it's the shared gateway socket.
