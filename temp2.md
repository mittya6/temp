はい、それはできます。curlでは「**SNI（Server Name Indication）としてexample.co.jpを使いつつ、実際にはALBのURLに接続する**」ということが可能です。

以下のようにすればOKです。

---

## ✅ curlで ALB に `example.co.jp` としてアクセスする構文

```bash
curl -v https://<ALBのDNS名> --resolve example.co.jp:443:<ALBのIPアドレス> --header "Host: example.co.jp"
```

または、DNS名をそのまま使うなら：

```bash
curl -v https://<ALBのDNS名> --header "Host: example.co.jp"
```

---

## 🔍 解説

| オプション                              | 説明                               |
| ---------------------------------- | -------------------------------- |
| `https://<ALBのDNS名>`               | 実際に接続する先（ALB）                    |
| `--header "Host: example.co.jp"`   | リクエストヘッダー内で「このFQDNでアクセスしています」と明示 |
| `--resolve example.co.jp:443:<IP>` | （任意）DNSの代わりに名前解決を固定する。ALBのIPを直指定 |

---

## 🔒 証明書の検証もしたいなら

ALBにはSNI対応があるため、証明書が `example.co.jp` に対して発行されたものであれば、上記のコマンドでも**正しい証明書が返される**はずです。

その証明書をcurl経由でチェックしたいなら、以下のように `--insecure` を**付けない** ことで、証明書検証も行われます：

```bash
curl -v https://<ALBのDNS名> --header "Host: example.co.jp"
```

証明書名が一致していないと以下のようなエラーが出ます：

```
SSL: no alternative certificate subject name matches target host name 'example.co.jp'
```

---

## ✅ opensslでの証明書確認もおすすめ

```bash
openssl s_client -connect <ALBのDNS名>:443 -servername example.co.jp
```

このコマンドでは **SNI として example.co.jp を指定して、どの証明書が返されるか確認** できます。

---

## まとめ

| やりたいこと                     | コマンド例                                                                |
| -------------------------- | -------------------------------------------------------------------- |
| `example.co.jp` としてリクエストする | `curl -v https://<ALBのDNS名> --header "Host: example.co.jp"`          |
| 証明書の中身を確認する                | `openssl s_client -connect <ALBのDNS名>:443 -servername example.co.jp` |

---

ブラウザの確認は難しくても、この `curl` や `openssl` の方法で、**本番FQDN向けACM証明書の設定確認**は可能です。

必要であれば、この手法を活かして**テスト用シェルスクリプト**のテンプレートもお作りできますよ。
