"""简易聊天室 — 基于 TCP 的最小聊天服务器/客户端，使用 loguru 日志。

用法:
  python simple_chat_room.py server    启动聊天服务器
  python simple_chat_room.py client    启动聊天客户端（可多个）

"""

import os
import random
import socket
import sys
import threading

from loguru import logger

HOST = "localhost"
PORT = 8080
BUFFER_SIZE = 4096  # 接收缓冲区大小


class Server:
    """TCP 聊天服务器 — 每个客户端一个线程。"""

    def __init__(self, host: str = HOST, port: int = PORT):
        self.clients: dict[socket.socket, str] = {}
        self.host = host
        self.port = port
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self) -> None:
        """绑定端口、监听，并在循环中接受客户端连接。"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        logger.info(f"服务器启动在 {HOST}:{PORT} 上, 等待连接")

        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                logger.info(f"{addr} 已连接到聊天室")
                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True,
                ).start()
        except KeyboardInterrupt:
            logger.info("正在关闭")
        finally:
            self.server_socket.close()

    def handle_client(self, client: socket.socket, addr: tuple) -> None:
        """处理一个客户端连接（在独立线程中运行）。"""
        nickname = ""
        try:
            nickname = client.recv(BUFFER_SIZE).decode("utf-8").strip()
            with self.lock:
                self.clients[client] = nickname
            self.broadcast(f"{nickname} 已上线")
            client.send(
                f"欢迎 {nickname}！输入 /quit 退出，/list 查看在线用户\n".encode("utf-8")
            )
            while True:
                data = client.recv(BUFFER_SIZE)
                if not data:
                    break
                message = data.decode("utf-8").strip()
                if message == "/quit":
                    break
                elif message == "/list":
                    with self.lock:
                        users = ", ".join(self.clients.values())
                    client.send(f"  在线用户: {users}\n".encode("utf-8"))
                else:
                    self.broadcast(f"[{nickname}]: {message}",client)
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            if client in self.clients:
                with self.lock:
                    del self.clients[client]
                self.broadcast(f"{nickname} 离开了聊天室")
                logger.info(f"[-] {addr} ({nickname}) 断开，当前在线: {len(self.clients)}")
            client.close()

    def broadcast(self, message: str, sender: socket.socket | None = None) -> None:
        """向所有已连接客户端广播 *message*，排除 *sender*。"""
        with self.lock:
            snapshot = list(self.clients.items())
        encoded = message.encode("utf-8")
        dead_clients: list[socket.socket] = []

        for sock, _name in snapshot:
            if sock is sender:
                continue
            try:
                sock.send(encoded)
            except OSError:
                dead_clients.append(sock)

        if dead_clients:
            with self.lock:
                for sock in dead_clients:
                    self.clients.pop(sock, None)


class Client:
    """TCP 聊天客户端。"""

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @staticmethod
    def _random_name() -> str:
        """生成一个简短的随机游客名称。"""
        return f"游客_{random.randint(1000, 9999)}"

    def start(self) -> None:
        """连接服务器并启动收发循环。"""
        try:
            self.socket.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            logger.error(f"错误: {e}, 无法连接到服务器 {self.host}:{self.port}")
            sys.exit(1)

        nickname = input("请输入你的名称: ").strip() or self._random_name()
        self.socket.send(nickname.encode("utf-8"))
        threading.Thread(target=self.receive, daemon=True).start()

        print(f"欢迎 {nickname}")
        try:
            while True:
                message = input()
                if message.strip():
                    self.socket.send(message.encode("utf-8"))
                    if message == "/quit":
                        break
        except (KeyboardInterrupt, EOFError):
            logger.info("正在退出")
        finally:
            self.socket.close()

    def receive(self) -> None:
        """接收线程 — 打印来自服务器的消息。"""
        while True:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    logger.info("与服务器断开连接")
                    break
                sys.stdout.write("\r\033[K" + data.decode("utf-8") + "\n")
                sys.stdout.write("> ")
                sys.stdout.flush()
            except (ConnectionResetError, OSError):
                break
        os._exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(0)

    mode = sys.argv[1].lower()
    if mode == "server":
        Server().start()
    elif mode == "client":
        Client().start()
    else:
        print(f"未知模式: {mode}")
