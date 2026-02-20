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

    @property
    def current(self):
        if self.current_name:
            return self.screens.get(self.current_name)
        return None

    def add(self, name, screen):
        self.screens[name] = screen
        screen.on_hide()

    def switch(self, name, **kwargs):
        if self.current:
            self.current.on_hide()
        self.current_name = name
        if self.current:
            self.current.on_show(**kwargs)

    def update(self):
        if self.current:
            self.current.update()

    def input(self, key):
        if self.current:
            self.current.input(key)
