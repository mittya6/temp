Concourse CIをローカル環境で構築するための `docker-compose.yml` ファイルですね。

Concourseは「Webノード（UIとAPI）」と「Workerノード（実際のタスクを実行）」に分かれており、これらが安全に通信するために**事前にSSHキーを生成しておく必要があります**。

以下の手順に沿ってセットアップを行ってください。

### 1. 認証キーの生成

まずはプロジェクトのディレクトリを作成し、その中でキーを生成します。ターミナルで以下のコマンドを順番に実行してください。

```bash
# キーを格納するディレクトリを作成
mkdir -p keys/web keys/worker

# Webノード用のキーを生成
ssh-keygen -t rsa -f ./keys/web/tsa_host_key -N ''
ssh-keygen -t rsa -f ./keys/web/session_signing_key -N ''

# Workerノード用のキーを生成
ssh-keygen -t rsa -f ./keys/worker/worker_key -N ''

# WebとWorkerが互いを認証できるように公開鍵をコピー
cp ./keys/worker/worker_key.pub ./keys/web/authorized_worker_keys
cp ./keys/web/tsa_host_key.pub ./keys/worker

```

---

### 2. `docker-compose.yml` の作成

同じディレクトリに `docker-compose.yml` という名前のファイルを作成し、以下の内容を貼り付けます。

```yaml
services:
  concourse-db:
    image: postgres:15
    environment:
      POSTGRES_DB: concourse
      POSTGRES_USER: concourse
      POSTGRES_PASSWORD: changeme
      PGDATA: /database
    volumes:
      - concourse-db:/database

  concourse-web:
    image: concourse/concourse:latest
    command: web
    depends_on:
      - concourse-db
    ports:
      - "8080:8080"
    volumes:
      - ./keys/web:/concourse-keys
    environment:
      CONCOURSE_POSTGRES_HOST: concourse-db
      CONCOURSE_POSTGRES_USER: concourse
      CONCOURSE_POSTGRES_PASSWORD: changeme
      CONCOURSE_POSTGRES_DATABASE: concourse
      CONCOURSE_EXTERNAL_URL: http://localhost:8080
      # 初期ユーザー名:パスワード
      CONCOURSE_ADD_LOCAL_USER: admin:test
      CONCOURSE_MAIN_TEAM_LOCAL_USER: admin
      CONCOURSE_CLUSTER_NAME: local-concourse
      CONCOURSE_SESSION_SIGNING_KEY: /concourse-keys/session_signing_key
      CONCOURSE_TSA_HOST_KEY: /concourse-keys/tsa_host_key
      CONCOURSE_TSA_AUTHORIZED_KEYS: /concourse-keys/authorized_worker_keys

  concourse-worker:
    image: concourse/concourse:latest
    command: worker
    privileged: true
    depends_on:
      - concourse-web
    volumes:
      - ./keys/worker:/concourse-keys
    environment:
      CONCOURSE_TSA_HOST: concourse-web:2222
      CONCOURSE_TSA_PUBLIC_KEY: /concourse-keys/tsa_host_key.pub
      CONCOURSE_TSA_WORKER_PRIVATE_KEY: /concourse-keys/worker_key

volumes:
  concourse-db:

```

---

### 3. 起動とアクセス

ファイルの準備ができたら、以下のコマンドでコンテナを起動します。

```bash
docker-compose up -d

```

起動後、ブラウザで **`http://localhost:8080`** にアクセスしてください。
右上の「login」から進み、`docker-compose.yml` で設定した以下の初期アカウントでログインできます。

* **ユーザー名:** `admin`
* **パスワード:** `test`

Workerの起動には少し時間がかかる場合があります。正常に接続されたかどうかは、Concourseにログイン後、Fly CLIツール（UI画面右下からダウンロード可能）を使って `fly -t main workers` コマンドを実行するか、UI上で確認できます。
