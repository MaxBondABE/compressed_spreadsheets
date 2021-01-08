import gzip
from time import time
from os import path
from typing import Iterable, Dict, List, Any, Optional

def hex_escape(c):
    return "%" + hex(ord(c))[2:]

SPECIAL_CHARS = (
        ("%", hex_escape("%")),
        (",", hex_escape(",")),
        ("\n", hex_escape("\n")),
        # % must be first - it must run first when escaping and last when
        # unescaping, or it will create erroneous escape sequences
        # If it does not run first when escaping, it will trample on escapes
        # we've already made; if it does not run last when unescaping, it
        # will create escape sequences the user didn't intend
)

class CompressedCSVFile(object):
    """
    Base class for CompressedDictReader, CompressedDictWriter.
    """

    def __init__(self, f, fieldnames, encoding="utf-8"):
        self.compressed_file = f
        self.fieldnames = fieldnames
        self.encoding = encoding

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        """
        Close the compressed file.

        When writing, it is critical to close the compressed file. Data will
        not be written to disk until the file is closed.
        """
        self.compressed_file.close()

    def escape(self, data: str) -> str:
        for char, escape in SPECIAL_CHARS:
            data = data.replace(char, escape)
        return data

    def unescape(self, data: str) -> str:
        for char, escape in SPECIAL_CHARS[::-1]:
            # Must iterate in reverse, see comment on SPECIAL_CHARS
            data = data.replace(escape, char)
        return data

    def encode_row(self, data: Iterable[str]) -> bytes:
        return b",".join(map(lambda s: self.escape(s).encode(self.encoding), data)) + b"\n"

    def decode_row(self, data: bytes) -> Iterable[str]:
        return map(self.unescape, data[:-1].decode(self.encoding).split(","))
        # Last character is newline, remove

class CompressedDictWriter(CompressedCSVFile):
    """
    Serialize flat dictionaries as compressed CSVs.
    The values may be any type with a __str__ method.
    Nested values are not supported.
    """

    @classmethod
    def open(cls, filename: str, fieldnames: List[str], encoding="utf-8", write_header=False, **gzipargs):
        """
        Open a compressed CSV for writing.

        :param fieldnames: The names of each column.
        :param encoding: The encoding to serialize strings to.
        :param skip_header: This parameter allows you to skip the header row if you
                            are using fieldtypes to define the field names, but the
                            sheet still has a header row.
        :param write_header: Write the header row to the CSV.
        :param gzipargs: Optional arguments to gzip.open()
        """
        return cls(gzip.open(filename, "w", **gzipargs), fieldnames, encoding, write_header)

    def __init__(self, f, fieldnames, encoding="utf-8", write_header=False):
        """
        :param fieldnames: The names of each column.
        :param encoding: The encoding to serialize strings to.
        :param skip_header: This parameter allows you to skip the header row if you
                            are using fieldtypes to define the field names, but the
                            sheet still has a header row.
        :param write_header: Write the header row to the CSV.
        :param gzipargs: Optional arguments to gzip.open()
        """
        super().__init__(f, fieldnames, encoding)
        if write_header:
            self.writeheader()

    def writeheader(self):
        """
        Write the header row to the CSV.
        """
        self.compressed_file.write(self.encode_row(self.fieldnames))

    def writerow(self, row: Dict[str, Any]):
        """
        Write a single row to the CSV.
        """
        self.compressed_file.write(self.encode_row(
            map(lambda name: str(row[name]), self.fieldnames))
        )

    def writerows(self, rows: Iterable[Dict[str, Any]]):
        """
        Write many rows to the CSV.
        """
        for row in rows:
            self.writerow(row)

class CompressedDictReader(CompressedCSVFile):
    """
    Deserialize flat dictionaries as compressed CSVs.
    Values are deserealized as strings unless the fieldtypes parameter is used.
    Nested values are not supported.
    """

    @classmethod
    def open(cls, filename: str, fieldnames: Optional[List[str]] = None,
            fieldtypes: Optional[Dict[str, Any]] = None,
            encoding="utf-8", skip_header=False,
            **gzipargs):
        """
        Open a compressed CSV for reading.

        :param fieldnames: The names of each column.
        :param fieldtypes: A dictionary mapping column names to types or functions
                           which perform the converstion to native Python types.
                           They should accept a string and return the desired type.
        :param encoding: The encoding to serialize strings to.
        :param skip_header: This parameter allows you to skip the header row if you
                            are using fieldtypes to define the field names, but the
                            sheet still has a header row.
        :param gzipargs: Optional arguments to gzip.open()
        """
        return cls(gzip.open(filename, **gzipargs), fieldnames, fieldtypes, encoding, skip_header)

    def __init__(self, f, fieldnames: Optional[List[str]] = None,
            fieldtypes: Optional[Dict[str, Any]] = None, encoding="utf-8",
            skip_header=False):
        """
        :param fieldnames: The names of each column.
        :param fieldtypes: A dictionary mapping column names to types or functions
                           which perform the converstion to native Python types.
                           They should accept a string and return the desired type.
                           If you supply fieldtypes without suppling fieldnames,
                           the keys to fieldtypes will be interpreted as the fieldnames.
        :param encoding: The encoding to serialize strings to.
        :param skip_header: This parameter allows you to skip the header row if you
                            are using fieldtypes to define the field names, but the
                            sheet still has a header row.
        """
        super().__init__(f, fieldnames, encoding)
        self.fieldtypes = fieldtypes

        if self.fieldnames is None:
            if fieldtypes is not None:
                self.fieldnames = self.fieldtypes.keys()
                if skip_header:
                    self.compressed_file.readline()
            else:
                self.fieldnames = tuple(self.decode_row(self.compressed_file.readline()))

        if self.fieldtypes is not None and set(self.fieldtypes.keys()) != set(self.fieldnames):
            raise ValueError("fieldtypes and fieldnames must contain the same set of names.")
        if self.fieldtypes is not None:
            self.load_row = self.load_row_with_types
        else:
            self.load_row = self.load_row_without_types

    def format_row(self, row: Iterable[str]) -> Dict[str, str]:
        """
        Build a dictionary, pairing the values in the row with the proper keys.
        """
        return {k: v for k,v in zip(self.fieldnames, row)}

    def cast_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert the values in the row dictionary to the proper type.
        """
        d = dict(row)
        return {k: cast(d[k]) for k,cast in self.fieldtypes.items()}

    def load_row_with_types(self, row: Iterable[str]) -> Dict[str, Any]:
        return self.cast_row(self.format_row(row))

    def load_row_without_types(self, row: Iterable[str]) -> Dict[str, Any]:
        return self.format_row(row)

    def load_row(self, row):
        raise NotImplementedError("Error: should have overwritten by __init__")

    def __next__(self):
        """
        Retrieve the next row in the CSV file.
        """
        line = self.compressed_file.readline()
        if not line:
            raise StopIteration()
        return self.load_row(self.decode_row(line))

    def __iter__(self):
        return self

__version__ = "1.0.1"

