# 画面作成

ボール転がしゲームに新しい画面（Screen）を追加する。

## 入力

$ARGUMENTS — 画面名と説明（例: "settings - 音量スライダーと操作設定の画面"）

## ルール

1. UIテキストは**日本語OK**（Noto Sans JPフォントを `ball_game.py` で設定済み）
2. Ursina組み込みUIコンポーネントを使う: `Text`, `Button`, `ButtonList`, `Slider`, `Sprite`
3. 装飾・静的ビジュアルには画像アセットを使う（`texture=` / `Sprite`、配置先: `game/desktop/assets/ui/`）
4. 全画面クラスは `screens.base` の `Screen` を継承する
5. 全エンティティは `self._add(entity)` で登録する（表示/非表示の自動管理のため）
6. 画面遷移は `self.manager.switch('画面名')` を使う
7. ESCキーは親画面に戻る動作にする
8. `on_show()` で `window.color` を設定して背景色を変える

## Screen基底クラスの仕様

```python
from screens.base import Screen
# Screen が提供するもの:
#   self.manager    — ScreenManager（self.manager.switch('名前', **kwargs) で画面遷移）
#   self.entities   — 自動管理されるエンティティリスト
#   self._add(e)    — エンティティを管理対象に登録（表示/非表示が自動化）
#   on_show(**kwargs) — 画面がアクティブになった時に呼ばれる（オーバーライド時はsuperを呼ぶ）
#   on_hide()       — 画面が非アクティブになった時に呼ばれる（オーバーライド時はsuperを呼ぶ）
#   update()        — アクティブ中、毎フレーム呼ばれる
#   input(key)      — アクティブ中、キーイベント時に呼ばれる
```

## テンプレート

```python
"""
{説明文}
"""

from ursina import Text, Button, color, window

from screens.base import Screen


class {クラス名}Screen(Screen):
    def __init__(self, manager):
        super().__init__(manager)

        # タイトル
        self._add(Text(
            text='{英語タイトル}',
            position=(0, 0.4),
            origin=(0, 0),
            scale=2.5,
            color=color.white,
        ))

        # ボタン・テキスト・画像など

    def on_show(self, **kwargs):
        super().on_show()
        window.color = color.rgb(30, 30, 50)

    def input(self, key):
        if key == 'escape':
            self.manager.switch('{戻り先の画面名}')
```

## 実行手順

1. `game/desktop/screens/{名前}.py` に画面クラスを作成する
2. `game/desktop/screens/__init__.py` にimportを追加する
3. `game/desktop/ball_game.py` に `manager.add('{名前}', {クラス名}Screen(manager))` を追加する
4. 画面遷移を接続する（どの画面からここに来るか、ESCでどこに戻るか）
5. 画像アセットが必要な場合は `game/desktop/assets/ui/` に必要なファイルを記載する

## 既存の画面一覧（参考）

| キー名 | クラス名 | 内容 |
|---|---|---|
| `start` | StartScreen | タイトル + Start/How to Play/Quit ボタン |
| `stage_select` | StageSelectScreen | モードタブ（Solo/Co-op/Versus）+ ステージ一覧 |
| `how_to_play` | HowToPlayScreen | 操作説明・ルール |
| `game` | GameScreen | 3Dゲームプレイ（盤面・ボール・物理演算） |
| `result` | ResultScreen | Clear/Game Over + Retry/Next Stage/Stage Select |

## 画面遷移フロー

```
Start → Stage Select → Game → Result
  ↓                              ↓
How to Play              Stage Select / Game（リトライ）
```
