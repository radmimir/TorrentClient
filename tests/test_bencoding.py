import unittest
from collections import OrderedDict

from bencode_torrent import bencoding


class TestBencodeDecoder(unittest.TestCase):
    def test_peek_existing(self):
        decoder = bencoding.BencodeDecoder(b"abc")

        self.assertEqual(b"a", decoder._peek())

    def test_peek_none(self):
        decoder = bencoding.BencodeDecoder(b"abc")
        decoder._index += 3

        self.assertEqual(None, decoder._peek())

    def test_not_bytes_string(self):
        with self.assertRaises(TypeError):
            bencoding.BencodeDecoder("abc")

        with self.assertRaises(TypeError):
            bencoding.BencodeDecoder(123)

        with self.assertRaises(TypeError):
            bencoding.BencodeDecoder([1, 2, 3])

    def test_increase_correct(self):
        decoder = bencoding.BencodeDecoder(b"abc")
        decoder._increase_index()

        self.assertEqual(1, decoder._index)

    def test_decode_integer(self):
        decoder = bencoding.BencodeDecoder(b"i123e")

        self.assertEqual(123, decoder.decode())

    def test__decode_bytes_string(self):
        decoder1 = bencoding.BencodeDecoder(b"4:abcd")
        decoder2 = bencoding.BencodeDecoder(b"0:")

        self.assertEqual(decoder1.decode(), b"abcd")
        self.assertEqual((decoder2.decode()), b"")

    def test_decode_list(self):
        decoder1 = bencoding.BencodeDecoder(b"l4:spam4:eggse").decode()
        decoder2 = bencoding.BencodeDecoder(b"le").decode()

        self.assertEqual(2, len(decoder1))
        self.assertEqual(b"spam", decoder1[0])
        self.assertEqual(b"eggs", decoder1[1])
        self.assertEqual(0, len(decoder2))
        self.assertEqual([], decoder2)

    def test_decode_dict(self):
        decoder = bencoding.BencodeDecoder(b"d9:publisher3:bob17:publisher-webpage15:www.example.come").decode()

        self.assertIsInstance(decoder, OrderedDict)
        self.assertEqual(decoder[b"publisher"], b"bob")
        self.assertEqual(decoder[b"publisher-webpage"], b"www.example.com")

    def test_common_decode(self):
        res = bencoding.BencodeDecoder(b"d3:catl3:Tom4:Jacke3:agei8ee").decode()

        self.assertEqual(res[b"cat"], [b"Tom", b"Jack"])
        self.assertEqual(res[b"age"], 8)


if __name__ == "__main__":
    unittest.main()
