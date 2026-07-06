"""
============================
聊天室 — 多线程 / 锁 / TCP / UDP 学习项目
============================

用法（在多个终端中分别运行）:
  python 聊天室.py tcp_server    启动 TCP 聊天服务器
  python 聊天室.py tcp_client    启动 TCP 聊天客户端（可开多个）
  python 聊天室.py udp_server    启动 UDP 聊天服务器
  python 聊天室.py udp_client    启动 UDP 聊天客户端（可开多个）

学习要点:
  1. TCP: 面向连接、可靠传输、三次握手
  2. UDP: 无连接、尽力交付、不保证顺序/到达
  3. threading.Thread: 每个客户端一个线程处理
  4. threading.Lock:  保护共享数据结构（客户端列表）
  5. socket 编程:     bind / listen / accept / connect / send / recv
"""

import socket
import threading
import sys
import os

# ============================================================================
# 全局配置
# ============================================================================
TCP_HOST = "127.0.0.1"
TCP_PORT = 8888

UDP_HOST = "127.0.0.1"
UDP_PORT = 9999

BUFFER_SIZE = 4096  # 接收缓冲区大小（字节）


# ============================================================================
# 第一部分：TCP 聊天服务器
# ============================================================================
# TCP 是面向连接的协议（类似打电话）:
#   1. 服务器 bind + listen
#   2. 客户端 connect（三次握手）
#   3. 建立连接后，双方通过 send/recv 收发数据
#   4. 关闭连接（四次挥手）
#
# 多线程:  每个客户端连接 = 1 个线程
# 锁:      多个线程同时操作 clients 字典，需要加锁保护

class TCPServer:
    def __init__(self, host=TCP_HOST, port=TCP_PORT):
        self.host = host
        self.port = port

        # -------------------------------------------
        # threading.Lock() — 互斥锁
        # 作用: 保证同一时刻只有一个线程能修改 clients 字典
        # 为什么需要: 多个客户端可能同时加入/离开，
        #             不加锁会导致数据竞争（race condition）
        # -------------------------------------------
        self.lock = threading.Lock()

        # 存储所有在线客户端: {socket: nickname}
        self.clients: dict[socket.socket, str] = {}

        # 创建 TCP socket
        # AF_INET  = IPv4
        # SOCK_STREAM = TCP（流式、可靠、有序）
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # SO_REUSEADDR: 允许重启服务器时立即复用端口（避免 TIME_WAIT 等待）
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        """启动服务器，进入主循环等待客户端连接"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  # 最大等待队列长度
        print(f"[TCP服务器] 启动在 {self.host}:{self.port}，等待连接...")

        try:
            while True:
                # accept() 阻塞等待客户端连接
                # 返回 (新socket, 客户端地址)
                client_socket, addr = self.server_socket.accept()
                print(f"[+] 新连接来自 {addr}")

                # 为每个客户端创建一个线程
                # daemon=True: 主线程退出时，该线程自动终止
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True,
                )
                thread.start()
                print(f"[*] 当前在线: {len(self.clients)} 人")
        except KeyboardInterrupt:
            print("\n[TCP服务器] 正在关闭...")
        finally:
            self.server_socket.close()

    def handle_client(self, client: socket.socket, addr):
        """处理单个客户端 — 运行在独立线程中"""
        nickname = None
        try:
            # 1. 接收昵称
            nickname = client.recv(BUFFER_SIZE).decode("utf-8").strip()
            if not nickname:
                nickname = f"匿名_{addr[1]}"

            # 2. 加锁 — 把新客户端加入字典
            with self.lock:  # with 语句自动 acquire/release，异常安全
                self.clients[client] = nickname

            # 3. 广播"加入"消息
            self.broadcast(f"🎉 [{nickname}] 加入了聊天室", sender=None)
            client.send(f"✅ 欢迎 {nickname}！输入 /quit 退出，/list 查看在线用户\n".encode("utf-8"))

            # 4. 循环接收消息
            while True:
                data = client.recv(BUFFER_SIZE)
                if not data:
                    break  # 客户端断开连接（recv 返回空字节）

                message = data.decode("utf-8").strip()

                if message == "/quit":
                    break
                elif message == "/list":
                    # 查看在线用户
                    with self.lock:
                        users = ", ".join(self.clients.values())
                    client.send(f"  在线用户: {users}\n".encode("utf-8"))
                elif message:
                    self.broadcast(f"[{nickname}]: {message}", sender=client)

        except (ConnectionResetError, ConnectionAbortedError, OSError):
            # 客户端异常断开
            pass
        finally:
            # 5. 客户端离开，清理资源
            if client in self.clients:
                with self.lock:
                    del self.clients[client]
                self.broadcast(f"👋 [{nickname}] 离开了聊天室", sender=None)
                print(f"[-] {addr} ({nickname}) 断开，当前在线: {len(self.clients)}")
            client.close()

    def broadcast(self, message: str, sender: socket.socket | None):
        """
        向所有客户端广播消息

        关键点: 用 lock 保护 clients 的读取，
                并且对 clients.values() 做快照（list()），
                避免遍历过程中字典被其他线程修改
        """
        with self.lock:
            # 做一份快照 — 这样即使其他线程修改字典，我们的遍历也不受影响
            snapshot = list(self.clients.items())

        encoded = message.encode("utf-8")
        dead_clients = []

        for sock, name in snapshot:
            if sock is sender:
                continue  # 不发给发送者本人（他自己的终端已经有输入了）
            try:
                sock.send(encoded)
            except OSError:
                dead_clients.append(sock)

        # 清理已断开的客户端
        if dead_clients:
            with self.lock:
                for sock in dead_clients:
                    self.clients.pop(sock, None)


# ============================================================================
# 第二部分：TCP 聊天客户端
# ============================================================================
# 客户端有两个并发任务:
#   1. 接收服务器消息并打印（receive 线程）
#   2. 读取用户键盘输入并发送（主线程）
# 这就是为什么需要多线程 — 不能让 recv 阻塞了用户输入，反过来也不行

class TCPClient:
    def __init__(self, host=TCP_HOST, port=TCP_PORT):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        """连接服务器并启动收发循环"""
        try:
            self.socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print(f"❌ 无法连接到服务器 {self.host}:{self.port}")
            sys.exit(1)

        # 1. 发送昵称
        nickname = input("请输入你的昵称: ").strip() or "匿名"
        self.socket.send(nickname.encode("utf-8"))

        # 2. 启动接收线程
        receive_thread = threading.Thread(target=self.receive, daemon=True)
        receive_thread.start()

        # 3. 主线程负责发送（读取用户输入）
        print(f"\n--- 欢迎 {nickname}！开始聊天吧 ---\n")
        try:
            while True:
                msg = input()
                if msg.strip():
                    self.socket.send(msg.encode("utf-8"))
                    if msg == "/quit":
                        break
        except (KeyboardInterrupt, EOFError):
            print("\n正在退出...")
        finally:
            self.socket.close()

    def receive(self):
        """接收服务器消息的线程"""
        while True:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    print("\n[与服务器断开连接]")
                    break
                # \r 清除当前行，让输出覆盖掉刚才的输入
                sys.stdout.write("\r\033[K" + data.decode("utf-8") + "\n")
                sys.stdout.write("> ")  # 重新显示输入提示
                sys.stdout.flush()
            except (ConnectionResetError, OSError):
                break
        os._exit(0)  # 接收线程挂了就退出整个进程


# ============================================================================
# 第三部分：UDP 聊天服务器
# ============================================================================
# UDP 是无连接协议（类似寄信）:
#   1. 不需要 connect，直接 sendto / recvfrom
#   2. 不保证送达、不保证顺序、不保证不重复
#   3. 每个数据包（datagram）是独立的
#   4. 因为没有"连接"的概念，服务器需要自己维护"已知客户端"列表
#
# 学习对比: 和 TCP 服务器对比，看看少了什么（accept, listen），
#           以及多了什么风险（丢包、乱序）

class UDPServer:
    def __init__(self, host=UDP_HOST, port=UDP_PORT):
        self.host = host
        self.port = port
        self.lock = threading.Lock()
        # 存储已知客户端: {addr: nickname}
        self.clients: dict[tuple[str, int], str] = {}

        # SOCK_DGRAM = UDP（数据报、无连接、不可靠）
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.socket.bind((self.host, self.port))
        print(f"[UDP服务器] 监听 {self.host}:{self.port}")

        try:
            while True:
                # recvfrom: 接收数据 + 发送方地址
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                message = data.decode("utf-8").strip()

                # 新客户端: 第一次收到该地址的消息 → 注册
                if addr not in self.clients:
                    with self.lock:
                        self.clients[addr] = message  # 第一条消息就是昵称
                    join_msg = f"🎉 [{self.clients[addr]}] 加入了UDP聊天室"
                    print(join_msg)
                    self.broadcast(join_msg, sender=addr)
                    self.socket.sendto(f"✅ 欢迎 {self.clients[addr]}！\n".encode("utf-8"), addr)
                    continue

                nickname = self.clients[addr]

                if message == "/quit":
                    with self.lock:
                        del self.clients[addr]
                    leave_msg = f"👋 [{nickname}] 离开了"
                    print(leave_msg)
                    self.broadcast(leave_msg, sender=addr)
                    self.socket.sendto("👋 再见！\n".encode("utf-8"), addr)

                elif message == "/list":
                    with self.lock:
                        users = ", ".join(self.clients.values())
                    self.socket.sendto(f"  在线用户: {users}\n".encode("utf-8"), addr)

                elif message:
                    chat_msg = f"[{nickname}]: {message}"
                    print(chat_msg)
                    self.broadcast(chat_msg, sender=addr)

        except KeyboardInterrupt:
            print("\n[UDP服务器] 关闭")
        finally:
            self.socket.close()

    def broadcast(self, message: str, sender: tuple[str, int] | None):
        """向所有已知客户端发送消息（UDP 版广播）"""
        with self.lock:
            snapshot = list(self.clients.keys())

        encoded = message.encode("utf-8")
        for addr in snapshot:
            if addr == sender:
                continue
            # UDP sendto: 每次发送都要指定目标地址
            # 没有连接，所以不能像 TCP 那样直接 send
            try:
                self.socket.sendto(encoded, addr)
            except OSError:
                pass  # UDP 不关心对方是否收到


# ============================================================================
# 第四部分：UDP 聊天客户端
# ============================================================================
# UDP 客户端的特殊之处:
#   - 没有 connect（也可以 connect，但那是"已连接UDP"，只影响内核路由优化）
#   - 发送用 sendto，接收用 recvfrom
#   - 因为无连接，客户端不知道服务器是否在线 —
#     消息发出去了，但不知道对方有没有收到

class UDPClient:
    def __init__(self, host=UDP_HOST, port=UDP_PORT):
        self.server_addr = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 绑定到随机端口（操作系统分配），这样服务器才能给我们回消息
        self.socket.bind(("", 0))
        self.running = True

    def start(self):
        nickname = input("请输入你的昵称: ").strip() or "匿名"

        # 用第一条消息作为"注册"（UDP 没有连接握手，直接发）
        self.socket.sendto(nickname.encode("utf-8"), self.server_addr)

        # 启动接收线程
        receive_thread = threading.Thread(target=self.receive, daemon=True)
        receive_thread.start()

        print(f"\n--- 欢迎 {nickname}！开始聊天吧（UDP模式）---\n")
        try:
            while self.running:
                msg = input()
                if msg.strip():
                    self.socket.sendto(msg.encode("utf-8"), self.server_addr)
                    if msg == "/quit":
                        self.running = False
                        break
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            self.socket.close()
            os._exit(0)

    def receive(self):
        """UDP 接收线程"""
        while self.running:
            try:
                data, _ = self.socket.recvfrom(BUFFER_SIZE)
                sys.stdout.write("\r\033[K" + data.decode("utf-8") + "\n")
                sys.stdout.write("> ")
                sys.stdout.flush()
            except OSError:
                if self.running:
                    break


# ============================================================================
# 第五部分：对比总结（运行 python 聊天室.py compare 查看）
# ============================================================================

def print_comparison():
    """打印 TCP vs UDP 对比表"""
    print("""
╔══════════════╦══════════════════════════╦══════════════════════════╗
║   特性       ║   TCP (SOCK_STREAM)       ║   UDP (SOCK_DGRAM)       ║
╠══════════════╬══════════════════════════╬══════════════════════════╣
║ 连接方式     ║ 面向连接 (connect)        ║ 无连接 (直接 sendto)     ║
║ 可靠性       ║ 可靠 (确认/重传/校验)     ║ 不可靠 (尽力交付)        ║
║ 顺序         ║ 保证有序                  ║ 不保证                   ║
║ 传输方式     ║ 字节流 (stream)           ║ 数据报 (datagram)        ║
║ 边界         ║ 无消息边界 (粘包)         ║ 有消息边界 (一个包一条)   ║
║ 开销         ║ 较高 (连接管理、确认)     ║ 较低 (只发不管)          ║
║ 适用场景     ║ 聊天、文件传输、网页      ║ 视频通话、DNS、游戏      ║
║ 服务器函数   ║ bind → listen → accept    ║ bind → recvfrom          ║
║ 客户端函数   ║ connect → send/recv        ║ sendto/recvfrom          ║
║ 粘包处理     ║ 需要自己定协议分帧        ║ 不需要 (天然有边界)      ║
╚══════════════╩══════════════════════════╩══════════════════════════╝

═══════════════ 锁 (Lock) 的作用 ═══════════════
  多个线程同时读写 clients 字典 → 数据竞争
  例如:
    线程A 正在遍历 clients 广播消息
    线程B 同时删除了一个断开客户端
    → 字典在遍历中被修改 → RuntimeError!
  解决方案:
    with self.lock:   # 互斥锁 — 同一时刻只有一个线程能进入
        ...

══════════════ 多线程模型 ═══════════════
  主线程:     accept() 等待新连接 → 创建子线程
  子线程 N:   handle_client() — 独立处理每个客户端
  为什么这样设计:
    - 如果单线程处理所有客户端，一个客户端阻塞（比如不发送数据）
      会导致 recv 卡住，其他客户端都无法收到新消息
    - 每个客户端一个线程，互不阻塞
    """)


# ============================================================================
# 入口
# ============================================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print_comparison()
        sys.exit(0)

    mode = sys.argv[1].lower()

    if mode == "tcp_server":
        TCPServer().start()

    elif mode == "tcp_client":
        TCPClient().start()

    elif mode == "udp_server":
        UDPServer().start()

    elif mode == "udp_client":
        UDPClient().start()

    elif mode == "compare":
        print_comparison()

    else:
        print(f"未知模式: {mode}")
        print(__doc__)
