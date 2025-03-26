Djangoには、`createsuperuser`コマンドのように直接一般ユーザを作成する公式コマンドはありません。しかし、自作の管理コマンドを作成すれば、同じようにコマンドラインから一般ユーザを作成できます。

---

### 一般ユーザ作成コマンドの作り方

#### 1. アプリケーションディレクトリに `management/commands` ディレクトリを作成
通常、アプリケーションフォルダの中に作ります。

```
myapp/
├── management/
│   └── commands/
│       └── createuser.py
└── __init__.py
```

#### 2. `__init__.py` ファイルを追加
`management` と `commands` フォルダに空の `__init__.py` を作成して、Pythonパッケージとして認識させます。

#### 3. `createuser.py` ファイルの中身
以下はユーザ作成用のカスタムコマンドのコードです。

**createuser.py**
```python
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a general user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the new user')
        parser.add_argument('password', type=str, help='Password for the new user')
        parser.add_argument('--email', type=str, default='', help='Email address for the new user')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        password = kwargs['password']
        email = kwargs['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'ユーザ "{username}" は既に存在します。'))
            return

        user = User.objects.create_user(username=username, password=password, email=email)
        self.stdout.write(self.style.SUCCESS(f'一般ユーザ "{username}" が作成されました。'))
```

---

### 4. 作成したコマンドを実行する
以下のように、`python manage.py` で一般ユーザを作成できます。

```bash
python manage.py createuser testuser mypassword --email=testuser@example.com
```

出力例：
```
一般ユーザ "testuser" が作成されました。
```

---

### ポイント
1. `BaseCommand` クラスを継承して独自コマンドを作成。
2. `add_arguments` メソッドで引数を指定。
3. `handle` メソッドでユーザ作成ロジックを実装。
4. `self.stdout.write` で出力メッセージを表示。

---

これで、スーパーユーザのようにコマンドラインから一般ユーザを作成できます！  
他に疑問やカスタマイズしたい部分があれば気軽に聞いてくださいね。
