# docker停止
sudo docker stop $(sudo docker ps -q)

# ボリューム群が格納されているディレクトリを圧縮してバックアップ
# ※ /home/user/backup/ の部分は、ご自身の環境の安全な退避先に書き換えてください
sudo tar -czvf /home/user/backup/docker_volumes_backup.tar.gz /var/lib/docker/volumes/


# dockerアンインストール
sudo systemctl stop docker
sudo apt-get remove docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Dockerリポジトリの無効化（または削除）
sudo rm /etc/apt/sources.list.d/docker.list

# アップグレード
sudo apt update
sudo apt upgrade -y
sudo apt dist-upgrade -y
sudo apt autoremove -y

# 
sudo do-release-upgrade


# dockerインストール
# 1. 必要な前提パッケージのインストール
sudo apt update
sudo apt install ca-certificates curl gnupg lsb-release

# 2. Dockerの公式GPGキーを追加
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 3. 22.04向けリポジトリのセットアップ
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Dockerエンジンのインストール
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
