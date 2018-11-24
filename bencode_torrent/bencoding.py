from collections import OrderedDict


# Индикатор начала данных типа "int"
TOKEN_INTEGER = b"i"

# Индикатор начала данных типа "list"
TOKEN_LIST = b"l"

# Индикатор начала числа типа "dict"
TOKEN_DICTIONARY = b"d"

# Индикатор конца числа типа "int"
TOKEN_END = b"e"


class BencodeDecoder(object):
    """
    Представляет последовательность байтов в стандартных типах данных Python
    """
    def __init__(self, data):
        if not isinstance(data, bytes):
            raise TypeError("Неверный формат переменной 'data'. Переменная должна иметь тип 'bytes'")
        else:
            self._data = data
            self._index = 0

    def decode(self):
        b_symbol = self._peek()
        if b_symbol is None:
            raise EOFError("В файле больше нет данных.")
        elif b_symbol == TOKEN_INTEGER:
            self._increase_index()
            return self._decode_integer()
        elif b_symbol == TOKEN_LIST:
            self._increase_index()
            return self._decode_list()
        elif b_symbol == TOKEN_DICTIONARY:
            self._increase_index()
            return self._decode_dict()
        elif b_symbol in b"0123456789":
            return self._decode_bytes_string()
        elif b_symbol == TOKEN_END:
            return None
        else:
            raise ValueError("Неверный токен или данные в файле по индексу %s" % str(self._index))

    def _peek(self):
        if self._index >= len(self._data):
            return None
        return self._data[self._index:self._index + 1]

    def _increase_index(self):
        self._index += 1

    def _decode_integer(self):
        return int(self._read_number(TOKEN_END))

    def _read_number(self, token):
        occurrence = self._data.index(token, self._index)
        result = self._data[self._index:occurrence]
        self._index = occurrence + 1
        return result

    def _decode_list(self):
        result = []
        while self._data[self._index:self._index + 1] != TOKEN_END:
            result.append(self.decode())
        self._increase_index()
        return result

    def _decode_dict(self):
        result = OrderedDict()
        while self._data[self._index:self._index + 1] != TOKEN_END:
            dict_key = self.decode()
            dict_value = self.decode()
            result[dict_key] = dict_value
        self._increase_index()
        return result

    def _decode_bytes_string(self):
        len_string = int(self._read_number(b":"))
        if self._index + len_string > len(self._data):
            raise IndexError("Индекс находится за пределами.")
        result = self._data[self._index:self._index + len_string]
        self._index += len_string
        return result
