結論だけ先に👇

oracledb v4.1.0 は古く、initOracleClient() もありません。Node 22 では最新版(6系)に上げてください。 
npm
+1

ただし接続先が Oracle Database 11g なので、6系の “Thin モード” は使えません（Thin は 12.1 以降のみ）。**“Thick モード”**で Instant Client を同梱して動かす必要があります。
Node-OracleDB
+1

対処手順（Lambda/Node.js 22 + Oracle 11g）

ドライバを 6.x に更新（Node 22 対応）

npm i oracledb@^6


6系はデフォルト Thin ですが、11g では不可のため Thick を明示します。
Node-OracleDB

Instant Client を Layer に入れる
Lambda のアーキ（x86_64 or arm64）と一致する Instant Client 19.x（Basic または Basic Light）をダウンロードし、/opt/oracle/instantclient_19_ に展開した ZIP を Layer 化します（AL2023 用に作り直し）。19.x クライアントは 11.2 以降のDBに接続可能です。
Oracle

環境変数を設定

LD_LIBRARY_PATH=/opt/oracle/instantclient_19_*/

可能なら PATH にも同ディレクトリを先頭追加
Thick はクライアントライブラリ（libclntsh.so 等）をこのパスから読み込みます。
Node-OracleDB

コード側で Thick を初期化

const oracledb = require('oracledb'); // v6+
oracledb.initOracleClient({ libDir: '/opt/oracle/instantclient_19_22' }); // 例
exports.handler = async () => {
  const conn = await oracledb.getConnection({
    user: process.env.DB_USER,
    password: process.env.DB_PASS,
    connectString: 'host.example.com:1521/ORCL' // いつものEZConnect等
  });
  const r = await conn.execute('select 1 from dual');
  await conn.close();
  return r.rows;
};


initOracleClient() は Thick 必須の初期化です（v6ドキュメント）。
Node-OracleDB

まだ DPI-1047 が出る場合のヒント

DPI_DEBUG_LEVEL=64 を環境変数に設定してロード探索ログを確認（どこを探しているかが出ます）。
Node-OracleDB

Lambda のアーキと Instant Client のアーキが一致しているか再確認。

よくある疑問

「Thinに上げれば楽と聞いた」
その通りですが、Thin は DB 12.1+ が前提。11g では NJS-116/NJS-138 相当のエラーになります。11gのままなら Thick 一択です。
Node-OracleDB
+1

「Instant Client のバージョンは？」
19.x を推奨（11.2+ サーバーに接続可能という互換性が明記されています）。
Oracle

「なぜ Node 18 では動いて Node 22 で壊れた？」
Node 22 で実行基盤が Amazon Linux 2023 に変わり、以前の Layer（AL2 向けビルド）では libclntsh.so を見つけられないため。Layer は AL2023 向けに作り直しが必要です。
Amazon Web Services, Inc.

これで直らなければ

使っている アーキ（x86_64/arm64）、Layer の 配置パス、実際の Instant Client ディレクトリ名（例：instantclient_19_22）を教えてください。

必要なら **最小構成のLayer ZIP（ディレクトリ構成と依存）**例をこちらで作ります。

あなた:
oracledb.initOracleClient({ libDir: '/opt/oracle/instantclient_19_22' }); // 例
AWS Lambdaのレイヤーでlibフォルダに格納しています。
その場合、パスはどのようになりますか？"/opt/oracle/instantclient_19_2"の部分は変更しなければならないんじゃないかと思います。
ChatGPT:

なるほど、良い視点です 👍
Lambda のレイヤーに展開したフォルダ構成にあわせて、libDir のパスは 実際の配置場所に合わせて指定しないといけません。

基本ルール

Lambda のレイヤーは /opt にマウントされます。

例えばレイヤー ZIP の中身がこうなっているとします：

layer.zip
└─ lib/
   └─ instantclient_19_22/
      ├─ libclntsh.so
      ├─ libnnz19.so
      └─ ...


→ この場合、Lambda 上では /opt/lib/instantclient_19_22/ が存在します。

コードでの指定例
oracledb.initOracleClient({ 
  libDir: '/opt/lib/instantclient_19_22' 
});

よくある間違い

Oracle のドキュメント例だと /opt/oracle/instantclient_19_22 になっていますが、これはレイヤーをそういう階層で作った場合の例です。

実際には、ZIP の展開先を確認して /opt/... 以下の正しいディレクトリを指定してください。

ls -R /opt を Lambda コンソール上の関数実行でログ出力させると確認できます。

確認ポイント

レイヤーZIPの階層構造（トップに lib/ を置いたか？それとも oracle/instantclient_19_22/？）

libclntsh.so が直接そのディレクトリにあるか？
→ 1つ上の階層を指してしまうと DPI-1047 が出ます。

👉 もしレイヤー ZIP の中身を tree や ls -R の出力で見せてもらえれば、正確な libDir の書き方を示せます。

フォルダ構成を教えていただけますか？

ChatGPT の回答は必ずしも正しいとは限りません。重要な情報は確認するよ
