from io import BytesIO
import tempfile
from os import path, remove, rmdir

from hypothesis import given
import hypothesis.strategies as st
from unittest.mock import MagicMock

from compressed_spreadsheets import *

@given(st.text())
def test_escape_and_unescape_are_inverse(string):
    csv = CompressedCSVFile(BytesIO(), tuple())
    assert csv.unescape(csv.escape(string)) == string

@given(st.lists(st.text(), min_size=1))
def test_encode_and_decode_are_inverse(row):
    csv = CompressedCSVFile(BytesIO(), tuple())
    assert list(csv.decode_row(csv.encode_row(row))) == row

@given(st.lists(st.text(), min_size=1))
def test_reading_and_writing_header_row(fieldnames):
    f = BytesIO()
    writer = CompressedDictWriter(f, fieldnames)
    writer.writeheader()

    f.seek(0)
    reader = CompressedDictReader(f)
    assert reader.fieldnames == tuple(fieldnames)

    f = BytesIO()
    writer = CompressedDictWriter(f, fieldnames, write_header=True)

    f.seek(0)
    reader = CompressedDictReader(f)
    assert reader.fieldnames == tuple(fieldnames)

@given(st.dictionaries(st.text(), st.text(), min_size=1))
def test_writing_and_reading_row(row):
    f = BytesIO()
    writer = CompressedDictWriter(f, row.keys(), write_header=True)
    writer.writerow(row)

    f.seek(0)
    reader = CompressedDictReader(f)
    assert next(reader) == row

@given(st.lists(st.lists(st.text(), min_size=5, max_size=5)))
def test_writing_and_reading_many_rows(rows):
    f = BytesIO()
    fieldnames = ("1", "2", "3", "4", "5")
    writer = CompressedDictWriter(f, fieldnames, write_header=True)
    for row in rows:
        row = {k: v for k,v in zip(fieldnames, row)}
        writer.writerow(row)

    f.seek(0)
    reader = CompressedDictReader(f)
    for row in rows:
        row = {k: v for k,v in zip(fieldnames, row)}
        assert next(reader) == row

@given(st.lists(st.lists(st.text(), min_size=5, max_size=5)))
def test_reader_is_iterable(rows):
    f = BytesIO()
    fieldnames = ("1", "2", "3", "4", "5")
    writer = CompressedDictWriter(f, fieldnames, write_header=True)
    for row in rows:
        row = {k: v for k,v in zip(fieldnames, row)}
        writer.writerow(row)

    f.seek(0)
    reader = CompressedDictReader(f)
    assert list(reader) == [{k: v for k,v in zip(fieldnames, row)} for row in rows]

def test_writing_and_reading_with_casting():
    f = BytesIO()
    row = {"a": 10}
    fieldnames = ("a", )
    fieldtypes = {"a": int}

    writer = CompressedDictWriter(f, fieldnames)
    writer.writerow(row)

    f.seek(0)
    reader = CompressedDictReader(f, fieldtypes=fieldtypes)
    assert dict(next(reader)) == row

def test_skipping_header_row():
    f = BytesIO()
    row = {"a": 10}
    fieldnames = row.keys()
    writer = CompressedDictWriter(f, fieldnames, write_header=True)
    writer.writerow(row)

    f.seek(0)
    reader = CompressedDictReader(f, fieldtypes={k: int for k in row.keys()}, skip_header=True)
    assert dict(next(reader)) == row

def test_open():
    directory = tempfile.mkdtemp()
    filename = path.join(directory, "temp.csv.gz")

    row = {"a": "b"}
    fieldnames = row.keys()
    writer = CompressedDictWriter.open(filename, fieldnames, write_header=True)
    writer.writerow(row)
    writer.close()

    reader = CompressedDictReader.open(filename)
    assert dict(next(reader)) == row

    remove(filename)
    rmdir(directory)

def test_context_manager_closes_files():
    CompressedCSVFile.close = MagicMock()

    f = BytesIO()
    row = {"a": "b"}
    fieldnames = row.keys()
    with CompressedDictWriter(f, fieldnames, write_header=True) as writer:
        writer.writerow(row)

    CompressedCSVFile.close.assert_called_once()

