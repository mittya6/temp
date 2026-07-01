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
