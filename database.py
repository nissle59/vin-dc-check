from dataclasses import dataclass
from typing import Optional

import asyncpg


class ConnectionDBError(Exception):
    ...


class DBNotConnected(Exception):
    ...


@dataclass
class AsyncDatabase:
    # входные данные
    host: str
    port: str
    user: str
    pswd: int
    database: str
    # соединение
    conn: Optional[asyncpg.Connection] = None

    async def _connect(self):
        if self.conn is not None:
            return True
        try:
            self.conn = await asyncpg.connect(host=self.host,
                                              port=self.port,
                                              user=self.user,
                                              password=self.pswd,
                                              database=self.database)
        except Exception as e:
            return e
        return True

    async def _disconnect(self):
        if self.conn is None:
            return True
        await self.conn.close(timeout=20)

    async def __aenter__(self):
        res = await self._connect()
        if res is True:
            return self
        raise ConnectionDBError(res)

    async def __aexit__(self, *args):
        await self._disconnect()

    async def fetch(self, query: str):
        if self.conn is None:
            raise DBNotConnected('Нет подключения к БД! Используйте в блоке async with!')

        try:
            res = await self.conn.fetch(query=query)
        except Exception as e:
            print(f'***\nОшибка при запросе к БД: {e}\n{query}\n***')
            return None

        return res

    async def execute(self, query: str) -> bool:
        if self.conn is None:
            raise DBNotConnected('Нет подключения к БД! Используйте в блоке async with!')

        try:
            res = await self.conn.execute(query=query)
        except Exception as e:
            print(f'***\nОшибка при запросе к БД: {e}\n{query}\n***')
            return None

        return res == 'COMMIT'
