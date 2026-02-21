"""
画面管理システム — Screen基底クラスとScreenManager
"""


class Screen:
    """全画面の基底クラス。エンティティの表示/非表示を自動管理する。"""

    def __init__(self, manager):
        self.manager = manager
        self.entities = []

    def _add(self, entity):
        """エンティティを管理対象に追加して返す"""
        self.entities.append(entity)
        return entity

    def on_show(self, **kwargs):
        for e in self.entities:
            e.enabled = True

    def on_hide(self):
        for e in self.entities:
            e.enabled = False

    def update(self):
        pass

    def input(self, key):
        pass


class ScreenManager:
    """画面の登録・切替を管理する"""

    def __init__(self):
        self.screens = {}
        self.current_name = None
        self._cursor = None
        self._webrtc = None
        self._cursor_screens = set()

    @property
    def current(self):
        if self.current_name:
            return self.screens.get(self.current_name)
        return None

    def set_cursor(self, cursor_handler, webrtc, cursor_screens):
        """仮想カーソルを設定する。cursor_screensに含まれる画面でのみカーソルを表示する。"""
        self._cursor = cursor_handler
        self._webrtc = webrtc
        self._cursor_screens = cursor_screens

    def add(self, name, screen):
        self.screens[name] = screen
        screen.on_hide()

    def switch(self, name, **kwargs):
        if self.current:
            self.current.on_hide()
        self.current_name = name
        if self.current:
            self.current.on_show(**kwargs)
        if self._cursor:
            if name in self._cursor_screens:
                self._cursor.show()
            else:
                self._cursor.hide()

    def update(self):
        if self.current:
            self.current.update()
        if self._cursor and self._webrtc and self.current_name in self._cursor_screens:
            self._cursor.update()
            for btn in self._webrtc.poll_buttons():
                if btn == 'confirm':
                    self._cursor.check_click(self.current.entities)
                elif btn == 'escape':
                    self.input('escape')

    def input(self, key):
        if self.current:
            self.current.input(key)
