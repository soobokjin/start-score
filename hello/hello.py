from iconservice import *

TAG = 'Hello'


class Hello(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._array_db = ArrayDB("array_db", db, value_type=str)
        self._dict_db = DictDB("dict_db", db, value_type=str, depth=1)
        self._var_db = VarDB("var_db", db, value_type=str)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()
    
    @external(readonly=True)
    def hello(self) -> str:
        Logger.debug(f'Hello, world!', TAG)
        return "Hello"

    @external(readonly=True)
    def getArray(self) -> list:
        return [d for d in self._array_db]

    @external
    def appendArray(self, data: str):
        self._array_db.put(data)

    @external(readonly=True)
    def getVar(self) -> str:
        return self._var_db.get()

    @external
    def setVar(self, data: str):
        self._var_db.set(data)

    @external(readonly=True)
    def getDict(self, key: str) -> str:
        return self._dict_db[key]

    @external
    def setDict(self, key: str, value: str):
        self._dict_db[key] = value
