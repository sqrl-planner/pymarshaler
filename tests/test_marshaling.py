import json
import unittest

from pymarshaler.errors import MissingFieldsError, UnknownFieldError
from pymarshaler.marshal import Marshal
from tests.test_classes import *
from tests.timed import timed

marshal = Marshal()


class TestNotFuturized:

    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.__dict__ == other.__dict__


class TestMarshalling(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        marshal = Marshal()

    @timed
    def test_not_futurized(self):
        test = TestNotFuturized('test')
        result = _marshall_and_unmarshall(TestNotFuturized, test)
        self.assertEqual(test, result)

    @timed
    def test_simple_marshalling(self):
        inner = Inner("Inner", 10)
        inner_result = _marshall_and_unmarshall(Inner, inner)
        self.assertEqual(inner, inner_result)

    @timed
    def test_nested_marshalling(self):
        inner = Inner("Inner", 10)
        inner_list = [Inner(f'Inner_{i}', i) for i in range(10)]
        outter = Outter(inner, inner_list)
        outter_result = _marshall_and_unmarshall(Outter, outter)
        self.assertEqual(outter, outter_result)

    @timed
    def test_multi_nested(self):
        inner = Inner("Inner", 10)
        inner_list = [Inner(f'Inner_{i}', i) for i in range(10000)]
        outter = Outter(inner, inner_list)
        multi_nested_outter = MultiNestedOutter(outter)
        result = _marshall_and_unmarshall(MultiNestedOutter, multi_nested_outter)
        self.assertEqual(result, multi_nested_outter)

    @timed
    def test_multi_nested_list(self):
        nested_list = MultiNestedList(
            [MultiNestedOutter(
                Outter(
                    Inner('Inner', x), [Inner('Inner', 1000)]
                )
            ) for x in range(10)]
        )
        result = _marshall_and_unmarshall(MultiNestedList, nested_list)
        self.assertEqual(result, nested_list)

    @timed
    def test_datetime_marshalling(self):
        class_with_date = ClassWithDate(datetime.datetime.now())
        result = _marshall_and_unmarshall(ClassWithDate, class_with_date)
        self.assertEqual(class_with_date, result)

    @timed
    def test_dict_marshalling(self):
        class_with_dict = ClassWithDict({'Test': Inner('inner', 1)})
        result = _marshall_and_unmarshall(ClassWithDict, class_with_dict)
        self.assertEqual(result, class_with_dict)

    @timed
    def test_nested_dict_marshalling(self):
        nested_dict = ClassWithNestedDict(
            {
                'nested1': ClassWithDict(
                    {
                        'Test': Inner('Inner', 1)
                    },
                ),
                'nested2': ClassWithDict(
                    {
                        'Test1': Inner('Inner', 1),
                        'Test2': Inner('Inner', 2)
                    }
                )
            }
        )
        result = _marshall_and_unmarshall(ClassWithNestedDict, nested_dict)
        self.assertEqual(nested_dict, result)

    @timed
    def test_fails_on_missing(self):
        self.assertRaises(MissingFieldsError, lambda: marshal.unmarshal(Inner, {'name': 'Inner'}))

    @timed
    def test_fails_on_unused(self):
        inner = Inner("Inner", 10)
        blob = json.loads(marshal.marshal(inner))
        blob['unused'] = 10
        self.assertRaises(UnknownFieldError, lambda: marshal.unmarshal(Inner, blob))

    @timed
    def test_ignores_unused(self):
        marshal = Marshal(ignore_unknown_fields=True)
        inner = Inner("Inner", 10)
        marshalled = marshal.marshal(inner)
        j = json.loads(marshalled)
        j['unused'] = 10
        result = marshal.unmarshal(Inner, j)
        self.assertEqual(result, inner)

    @timed
    def test_default_values(self):
        class_with_defaults = ClassWithDefaults()
        result = marshal.unmarshal(ClassWithDefaults, {})
        self.assertEqual(result, class_with_defaults)

    @timed
    def test_validate(self):
        self.assertRaises(ValidateError, lambda: marshal.unmarshal(ClassWithValidate, {}))

    @timed
    def test_custom_delegate(self):
        marshal.register_delegate(ClassWithCustomDelegate, lambda x: ClassWithCustomDelegate())
        result = marshal.unmarshal(ClassWithCustomDelegate, {})
        self.assertEqual(result, ClassWithCustomDelegate())

    @timed
    def test_nested_lists(self):
        nested_lists = NestedList([[Inner("Inner_1", 1)], [Inner("Inner_2", 2)]])
        result = _marshall_and_unmarshall(NestedList, nested_lists)
        self.assertEqual(nested_lists, result)

    @timed
    def test_nested_dict_list(self):
        nested = NestedDictList(
            {
                "Test1": {
                    "Test2": NestedList([[Inner("test", 1)], [Inner("test", 2)]])
                }
            }
        )
        result = _marshall_and_unmarshall(NestedDictList, nested)
        self.assertEqual(nested, result)

    @timed
    def test_walk_unknown(self):
        marshal = Marshal(True, True)
        blob = {
            'blah': {'name': 'foo', 'blah2': {'value': 1}}
        }
        result = marshal.unmarshal(Inner, blob)
        self.assertEqual(result, Inner('foo', 1))

    @timed
    def test_enums(self):
        enum = EnumClass.VAL
        result = _marshall_and_unmarshall(EnumClass, enum)
        self.assertEqual(result, enum)


def _marshall_and_unmarshall(cls, obj):
    marshalled = Marshal.marshal(obj)
    return marshal.unmarshal_str(cls, marshalled)


if __name__ == '__main__':
    unittest.main()
