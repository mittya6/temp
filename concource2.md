Windows環境向けのコマンドですね。Windows 10以降であれば標準で `ssh-keygen` がインストールされているため、標準のコマンドツールを使ってそのままキーを生成できます。

利用するツール（**コマンドプロンプト** または **PowerShell**）に合わせて、以下のコマンドをコピー＆ペーストして実行してください。

### コマンドプロンプト (cmd) の場合

一番シンプルで確実な方法です。コマンドプロンプトを起動し、以下のコマンドを順番に実行してください。

```cmd
:: キーを格納するディレクトリを作成
mkdir keys\web
mkdir keys\worker

:: Webノード用のキーを生成
ssh-keygen -t rsa -f keys\web\tsa_host_key -N ""
ssh-keygen -t rsa -f keys\web\session_signing_key -N ""

:: Workerノード用のキーを生成
ssh-keygen -t rsa -f keys\worker\worker_key -N ""

:: WebとWorkerが互いを認証できるように公開鍵をコピー
copy keys\worker\worker_key.pub keys\web\authorized_worker_keys
copy keys\web\tsa_host_key.pub keys\worker\

```

---

### PowerShell の場合

もしPowerShellをお使いの場合は、こちらを実行してください（ディレクトリ作成やコピーのコマンドが異なります）。

```powershell
# キーを格納するディレクトリを作成
New-Item -ItemType Directory -Force -Path keys\web, keys\worker

# Webノード用のキーを生成
ssh-keygen -t rsa -f keys\web\tsa_host_key -N '""'
ssh-keygen -t rsa -f keys\web\session_signing_key -N '""'

# Workerノード用のキーを生成
ssh-keygen -t rsa -f keys\worker\worker_key -N '""'

# WebとWorkerが互いを認証できるように公開鍵をコピー
Copy-Item keys\worker\worker_key.pub -Destination keys\web\authorized_worker_keys
Copy-Item keys\web\tsa_host_key.pub -Destination keys\worker\

```

**💡 補足事項**

* Windows版のDocker Desktopを使用している場合、生成されたキーファイルがそのままLinuxコンテナ（Concourse）にマウントされても、改行コードや権限の問題は通常Docker側で上手く吸収してくれます。
* 生成が完了したら、先ほどの `docker-compose.yml` を同じ階層（`keys` フォルダがあるのと同じディレクトリ）に配置して `docker-compose up -d` を実行してください。
