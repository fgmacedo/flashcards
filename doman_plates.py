# coding: utf-8
"""
Generate Glenn Doman method PDF files for words in an YAML file.

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

    python doman_plates.py words.yml
"""

import logging

logger = logging.getLogger()


def ensure_dir(dir_name):
    from pathlib import Path
    Path(dir_name).mkdir(parents=True, exist_ok=True)


def generate(group, words, config):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import landscape
    from reportlab.lib.colors import HexColor, PCMYKColor
    from reportlab.pdfbase.pdfmetrics import stringWidth

    output_file = f'{config.output_dir}/{group}.pdf'
    logger.info(f"Writting {len(words):0>3} words into '{output_file}'.")

    c = canvas.Canvas(output_file, pagesize=landscape(config.page_size))
    c.setTitle(f'{group.title()}')

    for word in words:
        font_size = config.font_size
        word = word.strip()
        word_width = stringWidth(word, config.font_name, font_size)
        if word_width / config.page_width > config.max_allowed_text_width_ratio:
            if config.disable_reduce_to_fit:
                logger.error(f"Failed to write '{group}/{word}': Larger than canvas.")
                continue
            else:
                logger.info(f"Reduced '{group}/{word}' font size to fit canvas.")
                font_size = reduce_font_size_to_fit(word, word_width, config)

        word_position = get_word_centered_position(config, font_size)

        c.setFont(config.font_name, font_size)
        # c.setFillColor(HexColor(f'0x{config.font_color}'))
        c.setFillColor(PCMYKColor(0, 100, 100, 0))
        c.drawCentredString(*word_position, word)
        c.showPage()
        yield word

    c.save()


def get_word_centered_position(config, font_size):
    from reportlab.pdfbase import pdfmetrics

    face = pdfmetrics.getFont(config.font_name).face
    ascent = (face.ascent * font_size) / 1000.0
    descent = (abs(face.descent) * font_size) / 1000.0
    font_height = ascent - descent
    center_width = config.page_width / 2
    center_height = config.page_height / 2 - font_height / 2
    return center_width, center_height


def extract_valid_words(words, already_seen_words, allow_repeated):
    if allow_repeated:
        return sorted(words)

    words_in_group = Counter(words)
    repeated_words = [word for word, count in words_in_group.items() if count > 1]
    if repeated_words and not allow_repeated:
        logger.warning(
            f"Ignored {len(repeated_words)} already seen word(s) in '{group}': {repeated_words}")

    words_in_group = set(words_in_group)
    new_words = words_in_group - already_seen_words
    ignored_words = words_in_group - new_words
    if ignored_words and not allow_repeated:
        logger.warning(
            f"Ignored {len(ignored_words)} already seen word(s) in '{group}': {ignored_words}")
    return sorted(new_words)


def reduce_font_size_to_fit(word, word_width, config):
    "Force brute reducing font size to fit width"
    reduction_safe_margin = 0.10
    reduce_ratio = config.page_width / word_width - reduction_safe_margin
    return config.font_size * reduce_ratio


def register_custom_font(config):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if not config.font_file:
        return

    pdfmetrics.registerFont(TTFont(config.font_name, config.font_file))


if __name__ == "__main__":
    import os
    import argparse
    from collections import Counter
    from copy import copy

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
        default="ff0000",
        help="Font color in hexadecimal. Defaults to RED (ff0000)."
    )
    parser.add_argument(
        "-pw",
        "--page_width",
        default=420,
        type=int,
        help="Page width in mm. Default to A3 width (420mm)."
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
            words = values.pop('words')
            for k, v in values.items():
                setattr(config, k, v)
        else:
            words = values

        ensure_dir(config.output_dir)
        register_custom_font(config)

        # update sizes to mm
        config.page_height = config.page_height * mm
        config.page_width = config.page_width * mm
        config.page_size = (config.page_height, config.page_width)

        words = extract_valid_words(words, already_seen_words, config.allow_repeated)

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

    logger.info(f"Wrote {total_words} words into {len(word_groups)} files.")
