Compressed Spreadsheets
-----------------------

Compressed Spreadsheets is a simple Python library for reading & writing to `gzip`
compressed CSV files using a similar API as the builtin `csv.DictReader` and `csv.DictWriter`.

# Priorities

* Simplicity
* Speed
* Ergonomics
    * Compatibility with the API of `DictReader` and `DictWriter` (though not
      the file format)

# Caveats

This code assumes that each row has to correct number of elements, in order to avoid
imposing checks on each row.

The goal of the implementation is to be reasonably fast with a simple implementation.
The CSVs it generates won't be compatible with any other library, because of the (simple, easy)
way special characters are escaped.

If we were to use `StringIO` to create a buffer that a real `DictWriter` instance
would write to, and then shuffle this into the compressed file, then we'd have
compatiblity without sacrificing simplicity; however, speed was more important
than compatiblity for my purposes, so I opted for this implementation.

The library does not behave well on sheets with 0 columns.

# Installation

## From GitHub

Simply download the project and place `compressed_spreadsheets.py` into your
project directory; it has no external requirements.

## From PyPI

`pip install compressed-spreadsheets`

# Examples

These examples enumerate common use cases. See the docstrings for full documentation.

## Writing to a spreadsheet

```
sheet = CompressedDictWriter.open("my_sheet.csv.gz", ("Column A", "Column B"))
sheet.writeheader()
sheet.writerow({"Column A": "Value 1", "Column B": "Value 2"})
sheet.writerows((
    {"Column A": "foo", "Column B": "bar"},
    {"Column A": "baz", "Column B": "snafu"}
))
sheet.close()
```

## Reading from a spreadsheet

Calling `CompressedDictReader.open(filename)` returns an object we can iterate over
to retrieve our rows.

```
sheet = CompressedDictReader.open("my_sheet.csv.gz")
# If the optional fieldnames argument is omitted, it is assumed the first line is a header row
next(sheet) # {"Column A": "Value 1", "Column B": "Value 2"}
for row in sheet:
    process(row)
```

## Specifying types for fields

The `fieldtypes` argument allows you to automatically convert values into their proper types.

```
write_sheet = CompressedDictWriter.open("my_numbers_sheet.csv.gz", fieldnames=("Column A", "Column B"))
write_sheet.writeheader()
write_sheet.writerow({"Column A": 10, "Column B": 5.1})
write_sheet.close()

read_sheet = CompressedDictReader.open("my_numbers_sheet.csv.gz", fieldtypes={"Column A": int, "Column B": float})
next(read_sheet) # {"Column A": 10, "Column B": 5.1})
```

## Context managers

Both `CompressedDictReader` and `CompressedDictWriter` can be used as context
managers. This will ensure the file is closed properly.

```
with CompressedDictWriter.open("my_sheet.csv.gz") as sheet:
    for row in data:
        sheet.writerow(row)
```

# Contributing

I'm open to contributions, and especially open to bug reports. Please open an
issue for any bugs, and please include unit tests & docstrings for any pull requests.

Use `pip -r development.txt` to install the testing dependencies. Run tests with
`pytest`. If you've made a very significant change or you'd like to hear for computer
fan, you can use `pytest --hypothesis-profile hammer` to generate 1000 testcases
for each test.

# License

Compressed Spreadsheets is distributed under the MIT license. See
LICENSE.txt for the full terms of the license.
