"""Measure answer bodies without interpreting their factual or theoretical quality."""

import argparse
import json
from pathlib import Path
import re


INTERNAL_CODES = re.compile(r'(?<![A-Za-z0-9])(?:S[0-6](?:—S[0-6])?|X0|G\d+|CM-[A-Z]+|IT\d|IG\d|DF\d|M\d|R[1-7]|CAS-[A-Z]+)(?![A-Za-z0-9])')
METHOD_NOTE = re.compile(r'(?m)^[ \t]*(?:\*\*)?方法附注(?:\*\*)?[:：](?:\*\*)?[^\n]*(?:\n[ \t]*)*\Z')
NEGATIVE_WORDS = re.compile(r'不能|不得|不等于|不代表|不是|不会|不应|不必|无需|并非|未必|不可|不宜|不构成|不意味|不作为|不把|不将|不要')


def answer_body(text):
    match = METHOD_NOTE.search(text)
    return text[:match.start()].rstrip(' \t\r\n') if match else text


def measure(text):
    body = answer_body(text)
    sentences = sum(bool(part.strip()) for part in re.split(r'[。！？]', body))
    negatives = len(NEGATIVE_WORDS.findall(body))
    return {'characters': len(body), 'sentences': sentences,
            'negative_words': negatives,
            'negatives_per_sentence': negatives / sentences if sentences else None,
            'paragraphs': sum(bool(part.strip()) for part in re.split(r'\n\s*\n', body)),
            'internal_codes': INTERNAL_CODES.findall(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('answer', type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.answer.read_text(encoding='utf-8-sig')), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
