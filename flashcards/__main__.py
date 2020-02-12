# coding: utf-8
"""
Generate Glenn Doman flash cards PDF files for words in an YAML file.

Requirements:
    pip install pyyaml reportlab

Example 'words.yml':
    corpo_humano:
    - pé
    - mão
    - orelha
    - braço

    animais:
    - cachorro
    - vaca
    - ovelha
    - cabra
    - elefante
    - girafa
    - coelho
    - urubu

    insetos:
    - formiga
    - aranha
    - mosquito
    - mosca

Usage:

    python -m flashcards words.yml
"""

import os
import argparse
import logging
import re
import math
from copy import copy

from .flashcards import (
    generate,
    generate_math,
    ensure_dir,
    register_custom_font,
    extract_valid_words,
    generate_math,
)

logger = logging.getLogger(__name__)


COLOR_HEXA_PATTERN = re.compile(r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})')
COLOR_CMYK_PATTERN = re.compile(r'(\d+,\d+,\d+,\d+)')


def parse_color(value):
    from reportlab.lib.colors import HexColor, PCMYKColor
    match = COLOR_HEXA_PATTERN.search(value)
    if match:
        hex = match.group(1).lower()
        return HexColor(f'0x{hex}')
    match = COLOR_CMYK_PATTERN.search(value)
    if match:
        cmyk = [int(x) for x in match.group(1).split(",")]
        return PCMYKColor(*cmyk)
    raise ValueError(f"The '{value}' is not a valid color.")


if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("pyyaml is required. Try: pip install pyyaml")

    try:
        from reportlab.lib.units import mm
    except ImportError:
        print("reportlab is required. Try: pip install reportlab")

    parser = argparse.ArgumentParser(description='Generate Glenn Doman PDF files for words.')
    parser.add_argument(
        "file",
        help="YAML file with words to generate PDFs. The root level should be a group that will"
             " be used as the output file name."
    )
    parser.add_argument(
        "-fs",
        "--font_size",
        default=250,
        type=int,
        help="Font size."
    )
    parser.add_argument(
        "-fn",
        "--font_name",
        default="Helvetica",
        help="Font name."
    )
    parser.add_argument(
        "-ff",
        "--font_file",
        help="Font file that matches a custom 'font_name'."
    )
    parser.add_argument(
        "-fc",
        "--font_color",
        default="0,100,100,0",
        type=parse_color,
        help=(
            "Font color in hexadecimal (eg. #ff0000) or in CMYK (eg. 0,100,100,0). "
            "Defaults to CMYK red (0,100,100,0)."
        )
    )
    parser.add_argument(
        "-pw",
        "--page_width",
        default=440,
        type=int,
        help="Page width in mm. Default to A3 width (440mm)."
    )
    parser.add_argument(
        "-ph",
        "--page_height",
        default=99,
        type=int,
        help="Page height in mm. Default to one third of A3 height (99mm)."
    )
    parser.add_argument(
        "-mr",
        "--max_allowed_text_width_ratio",
        default=0.95,
        type=float,
        help=(
            "Max ratio between text width and the available canvas width. When text is larger "
            "than allowed, it will be ignored or reduced accordingly with `disable_reduce_to_fit`"
        )
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        default='out',
        help="Directory where the PDFs will be generated."
    )
    parser.add_argument(
        "-wps",
        "--words_per_sheet",
        default=3,
        type=int,
        help="""The number of words per real sheet used for print. Set any number > 0
        to optimize paper usage. Defaults to 3 since the default page size is 1/3 of an A3."""
    )
    parser.add_argument(
        "-ar",
        "--allow_repeated",
        action='store_true',
        help="Allow repeated words."
    )
    parser.add_argument(
        "-drf",
        "--disable_reduce_to_fit",
        action='store_true',
        help=(
            "Disable reducing larger words to fit canvas. "
            "When disabled, text larger than canvas will be ignored."
        )
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    if not os.path.exists(args.file):
        raise ValueError("You must inform a valid YAML file.")

    with open(args.file, "r") as f:
        word_groups = yaml.safe_load(f)

    total_words = 0
    already_seen_words = set(["", None])
    for group, values in sorted(word_groups.items(), key=lambda x: x[0]):
        config = copy(args)

        if isinstance(values, dict):
            words = values.pop('words', None)
            for k, v in values.items():
                if k == 'font_color':
                    v = parse_color(v)
                setattr(config, k, v)
        else:
            words = values

        ensure_dir(config.output_dir)
        register_custom_font(config)

        # update sizes to mm
        config.page_height = config.page_height * mm
        config.page_width = config.page_width * mm
        config.page_size = (config.page_height, config.page_width)

        if hasattr(config, 'math'):
            generate_math(group, config)
            continue

        words, invalid = extract_valid_words(words, already_seen_words, config.allow_repeated)
        if invalid and not config.allow_repeated:
            logger.warning(
                f"Ignored {len(invalid)} already seen word(s) in '{group}': {invalid}"
            )

        if config.words_per_sheet:
            remainder = len(words) % config.words_per_sheet
            if remainder != 0:
                missing = config.words_per_sheet - remainder
                logger.warning(
                    f"Group '{group}' has less words than ideal for paper usage "
                    f"({config.words_per_sheet}), missing {missing} words"
                )

        generated = list(generate(group, words, config))

        total_words += len(generated)
        already_seen_words = already_seen_words.union(set(generated))

    total_sheets = math.ceil(total_words / config.words_per_sheet)
    logger.info(
        f"Wrote {total_words} words into {len(word_groups)} files. "
        f"Expect to use near {total_sheets} sheets."
    )
