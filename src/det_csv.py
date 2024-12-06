import chardet
"""
This script detects the encoding of a given CSV file using the `chardet` library.

The script performs the following steps:
1. Imports the `chardet` library.
2. Defines the path to the CSV file (`data.csv`).
3. Opens the CSV file in binary read mode.
4. Uses `chardet.detect()` to detect the encoding of the file content.
5. Prints the result, which includes the detected encoding, confidence level, and language (if applicable).

Attributes:
    csv_file (str): The path to the CSV file to be analyzed.

Usage:
    Run this script to detect and print the encoding of the specified CSV file.
"""

csv_file = '../data/data.csv'

with open(csv_file, 'rb') as f:
    result = chardet.detect(f.read())
    print(result)