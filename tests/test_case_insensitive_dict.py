import unittest

from kibom.case_insensitive_dict import CaseInsensitiveDict

class DictTest(unittest.TestCase):
    def setUp(self):
        self.d = {"a": 1, "B": 2}
        self.d1 = CaseInsensitiveDict({"a": 1, "B": 2})
        self.d2 = CaseInsensitiveDict()
        self.d2["A"] = 1
        self.d2["b"] = 2

    def test_init(self):
        d = CaseInsensitiveDict()
        self.assertFalse(d)

        d["a"] = 1
        d["B"] = 2
        self.assertTrue(d)

        d = CaseInsensitiveDict({"a":1, "B":2})
        self.assertTrue(d)

    def test_length(self):
        d = CaseInsensitiveDict()

        self.assertEqual(len(d), 0)
        d["A"] = 1
        d["b"] = 2
        self.assertEqual(len(d), 2)
        d.pop("a")
        self.assertEqual(len(d), 1)
        del d["B"]
        self.assertEqual(len(d), 0)

    def test_contains(self):
        self.assertIn("B", self.d1)
        self.assertIn("b", self.d1)
        self.assertIn("B", self.d2)
        self.assertIn("b", self.d2)

    def test_items(self):
        self.assertTrue(self.d1 == self.d2)

    def test_keys(self):
        self.assertEqual(self.d1.keys(), self.d2.keys())

    def test_values(self):
        self.assertEqual(
            [v for v in self.d1.values()],
            [v for v in self.d2.values()])

    def test_preserve_keys(self):
        d1 = CaseInsensitiveDict({"a": 1, "B":2})
        d2 = CaseInsensitiveDict({"a": 1, "B": 2})
        d2["A"] = 1
        self.assertEqual(d1.keys(), d2.keys())

    def test_equality_with_dict(self):
        self.assertTrue(self.d == self.d1)
        self.assertTrue(self.d1 == self.d)

    def test_conversion_to_dict(self):
        d = dict(self.d1)
        self.assertTrue(self.d == d)
        d2 = dict(CaseInsensitiveDict({key.swapcase: value for key, value in self.d.items()}))
        self.assertFalse(self.d == d2)

    def test_str_conversion(self):
        d = CaseInsensitiveDict({"a": 1, "B": 2})
        self.assertEqual(str(d), "{'a': 1, 'B': 2}")
        self.assertEqual(repr(d), f"{CaseInsensitiveDict.__name__}({{'a': 1, 'B': 2}})")

    def test_deep_copy(self):
        d1 = CaseInsensitiveDict({"a": 1, "B": 2})
        d2 = d1.copy()
        self.assertEqual(d1, d2)
        d2.pop("a")
        self.assertIn("a", d1)
        self.assertNotEqual(d1, d2)

    def test_shallow_copy(self):
        d1 = CaseInsensitiveDict({"a": 1, "B": 2})
        d2 = d1
        d2.pop("b")
        self.assertNotIn("B", d1)


if __name__ == '__main__':
    unittest.main()
