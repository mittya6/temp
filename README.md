了解。kubeadm で作ったクラスタが「connection refused :443」で叩けない＆証明書が怪しいときの“復旧手順（単一コントロールプレーン/自己署名CA想定）”を最短でまとめます。
※ 途中のコマンドは**コントロールプレーンノード**で実施、基本 `sudo` 必須です。

# 手順（チェック → 更新 → 再起動 → 確認）

## 0) まず基本確認

```bash
# kubelet が落ちていないか
sudo systemctl status kubelet

# ログ live で確認（エラーがあれば控える）
sudo journalctl -u kubelet -f
```

## 1) 証明書の有効期限を確認

```bash
sudo kubeadm certs check-expiration
```

* 期限切れが出るなら次へ。

## 2) コントロールプレーンの証明書を更新

```bash
# すべて更新（自己署名CAを使っている一般的な構成）
sudo kubeadm certs renew all
```

> ここで「/etc/kubernetes/pki/ca.key: permission denied（or not found）」が出る場合
>
> * `sudo` を付けているか確認
> * **ca.key が無い**なら、kubeadm 管理の CA を紛失している状態です。既存 CA での更新は不可なので、後述の「トラブル対処」を参照してください。

## 3) kubeconfig（admin.conf など）も更新（期限切れ対策）

```bash
sudo kubeadm init phase kubeconfig all
```

その後、kubectl 用にコピー：

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

## 4) kubelet 再起動（静的Podの再作成を促す）

```bash
sudo systemctl restart kubelet
# 数十秒待つ
```

## 5) API サーバ接続先（ポート）を確認

通常 kubeadm の API サーバは **:6443** です。`~/.kube/config` が **:443** を向いていると接続拒否になりがち。

```bash
# 接続先URLを確認（server: の行）
grep -n 'server:' $HOME/.kube/config
```

* `https://<IPまたはLB名>:6443` になっていなければ、`admin.conf` をコピーし直すか修正してください。
* 逆に、意図的に LB の **:443** 経由なら、その LB が :443→:6443 へ正しく転送しているか（ヘルスチェック/セキュリティグループ/ファイアウォール）を見直してください。

## 6) 状態確認

```bash
# まずクラスタ情報
kubectl cluster-info

# コアPodの立ち上がりを確認
kubectl get pods -n kube-system

# 目標コマンド
kubectl get nodes
```

# それでもダメな場合の追加チェック

### A) apiserver が起動しているか

```bash
# コンテナランタイムが containerd の場合
sudo crictl ps | grep kube-apiserver

# docker の場合
sudo docker ps | grep kube-apiserver
```

出ていない場合は `/etc/kubernetes/manifests/kube-apiserver.yaml` のエラー（証明書パス/SAN/引数）が原因のことが多いです。編集ミスがあれば戻して `kubelet` 再起動。

### B) SAN の不足（エンドポイントを変えた/増やした）

LB 名や新IPでアクセスしたいのに証明書の SubjectAltName に入っていないと TLS で弾かれます。
`--apiserver-cert-extra-sans <IP/DNS>` を付けて証明書再発行が必要です（kubeadm の設定ファイルに追記→再発行）。

### C) ワーカーノードの kubelet クライアント証明書が期限切れ

コントロールプレーン復旧後も Node が NotReady のときは、各ノードで以下を実施して再発行を促します：

```bash
# 各ノードで
sudo systemctl stop kubelet
sudo rm -f /var/lib/kubelet/pki/kubelet-client-*.pem /var/lib/kubelet/pki/kubelet-client-current.pem
sudo systemctl start kubelet
```

（API サーバが上がっていれば kubelet の証明書ローテーションが再開します）

# よくあるハマり所

* **`:443` に向いている**
  kubeadm デフォルトは **`:6443`**。意図して 443 を使う場合は LB/Ingress で TLS/ポートの中継が正しいか確認。

* **`ca.key` の権限/所在エラー**
  実行は必ず `sudo`。ファイルは `/etc/kubernetes/pki/ca.key`。紛失していると `kubeadm certs renew` は使えません。

* **時刻ずれ**
  証明書検証は時刻に敏感。`timedatectl` で NTP 同期を確認。

# （重要）CA を紛失していた場合の方針

`/etc/kubernetes/pki/ca.key` を失った場合、既存 CA での通常更新は不可です。選択肢は：

1. **バックアップから CA を戻す**（最良）
2. **新しい CA で再発行**

   * apiserver などコントロールプレーン証明書と kubeconfig を新CAで作り直す
   * 既存ノードとは信頼関係が切れるため、ノード再ジョイン（`kubeadm reset` → `kubeadm join`）が必要になることがあります

---

この手順で多くの「期限切れ→接続拒否」を復旧できます。
進めてみて、どこでエラーになったか（コマンド結果の先頭数行）を貼ってくれれば、そこからピンポイントで詰めます。
