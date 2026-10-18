"""Measure answer bodies without interpreting their factual or theoretical quality."""

import argparse
import json
from pathlib import Path
import re


INTERNAL_CODES = re.compile(r'(?<![A-Za-z0-9])(?:S[0-6](?:—S[0-6])?|X0|G\d+|CM-[A-Z]+|IT\d|IG\d|DF\d|M\d|R[1-7]|CAS-[A-Z]+)(?![A-Za-z0-9])')
METHOD_NOTE = re.compile(r'(?m)^[ \t]*(?:\*\*)?方法附注(?:\*\*)?[:：](?:\*\*)?[^\n]*(?:\n[ \t]*)*\Z')


def answer_body(text):
    return METHOD_NOTE.sub('', text).strip()


def measure(text):
    body = answer_body(text)
    return {'characters': len(body), 'internal_codes': INTERNAL_CODES.findall(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('answer', type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.answer.read_text(encoding='utf-8-sig')), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
