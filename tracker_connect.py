import logging
import random
import socket
from struct import unpack
from urllib.parse import urlencode

import aiohttp


class TrackerResponse:
    """
        Ответ от трекера после успешного подсоединения к url.
        Может вернуть ошибку даже если соединение прошло успешно(описано в faliure).
       """

    def __init__(self, response: dict):
        self.response = response

    @property
    def failure(self):  # Вернет сообщение об ошибке в случае ошибки и None - если все хорошо.
        if b"failure reason" in self.response:
            return self.response[b"failure reason"].decode("utf-8")
        return None

    @property
    def interval(self) -> int:  # Интервал ожидания отправки запросов на сервер в секундах
        return self.response.get(b"interval", 0)

    @property
    def complete(self) -> int:  # Количество пиров для целого файла - сиды
        return self.response.get(b'complete', 0)

    @property
    def incomplete(self) -> int:  # Количество пиров - не сидов - личи
        return self.response.get(b'incomplete', 0)

    @property
    def peers(self):  # список кортежей для каждого пира вида (ip,port)
        # The BitTorrent specification specifies two types of responses. One
        # where the peers field is a list of dictionaries and one where all
        # the peers are encoded in a single string
        peers = self.response[b'peers']
        if type(peers) == list:
            # TODO Implement support for dictionary peer list
            logging.debug('Dictionary model peers are returned by tracker')
            raise NotImplementedError()
        else:
            logging.debug('Binary model peers are returned by tracker')
            # Разделяем строку на подстроки длиной 6 байт, где
            # первые 4 символа - ip адрес, последние 2 - tcp - port
            peers = [peers[i:i + 6] for i in range(0, len(peers), 6)]

            # Convert the encoded address to a list of tuples
            return [(socket.inet_ntoa(p[:4]), _decode_port(p[4:]))  # передаем ip и порт в представлении
                    for p in peers]  # (192.168.12.12, 8080)

    def __str__(self):
        return "incomplete: {incomplete}\n" \
               "complete: {complete}\n" \
               "interval: {interval}\n" \
               "peers: {peers}\n".format(
            incomplete=self.incomplete,
            complete=self.complete,
            interval=self.interval,
            peers=", ".join([x for (x, _) in self.peers]))


class Tracker:
    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = _calculate_peer_id()
        self.http_client = aiohttp.ClientSession()

    async def connect(self,
                      first=None,
                      uploaded=0,
                      downloaded=0
                      ):

        """
                Производит запрос на трекер для обновления статистики и получает
                список доступных для подключения пиров.
                Если запрос успешен, список пиров будет обновлен в результате вызова
                этой функции.
                first - флаг первого запроса
                uploaded - сумарное количество выгруженных байт
                downloaded - суммарное количество скачанных байт
        """
        params = {
            'info_hash': self.torrent.info_hash,  #
            'peer_id': self.peer_id,
            'port': 6889,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': self.torrent.total_size - downloaded,
            'compact': 1}
        if first:
            params["event"] = "started"
        url = self.torrent.announce + "?" + urlencode(params)
        logging.info("Connected to tracker. Url: " + url)
        async with self.http_client.get(url) as response:
            if response.status != 200:
                raise ConnectionError("Unable to connect to tracker")
            data = await response.read()
            return TrackerResponse(bencoding.Decode(data).decode())


def _calculate_peer_id():  # Генерирует id клиента
    return "-PC0001-" + ''.join([str(random.randint(0, 9)) for _ in range(12)])


def _decode_port(port):  # Преобразует 32-битный упакованный номер порта в int
    return unpack(">H", port)[0]
