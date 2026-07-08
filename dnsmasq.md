
```
version: '3.8'

services:
  dnsmasq:
    image: strm/dnsmasq
    container_name: dnsmasq
    ports:
      - "53:53/udp"
      - "53:53/tcp"
    volumes:
      - ./dnsmasq.conf:/etc/dnsmasq.conf:ro
    cap_add:
      - NET_ADMIN
    restart: unless-stopped
```

dnsmasq.conf
```
# --- 基本設定 ---
# 外部の名前解決に使用する上流のDNSサーバーを指定 (例: Google Public DNS, Cloudflare)
server=8.8.8.8
server=1.1.1.1

# ホスト名にドメインが含まれていない場合、上位のDNSサーバーに転送しない
domain-needed

# プライベートIPアドレスの逆引きを上位DNSサーバーに転送しない
bogus-priv

# --- カスタムDNSレコード（ローカルの名前解決） ---
# 特定のドメインをローカルのIPアドレスに向ける設定
# 書式: address=/ドメイン名/IPアドレス
address=/router.local/192.168.1.1
address=/nas.local/192.168.1.10
address=/test.example.com/192.168.1.50
```
