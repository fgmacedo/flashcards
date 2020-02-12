# coding: utf-8
import logging
import math
import random
from collections import Counter

logger = logging.getLogger(__name__)


def ensure_dir(dir_name):
    from pathlib import Path
    Path(dir_name).mkdir(parents=True, exist_ok=True)


def generate(group, words, config):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import landscape
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
        c.setFillColor(config.font_color)
        c.drawCentredString(*word_position, word)
        c.showPage()
        yield word

    c.save()


def generate_math(group, config):
    import numpy as np
    from alive_progress import alive_bar
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import landscape
    from reportlab.pdfbase.pdfmetrics import stringWidth

    output_file = f'{config.output_dir}/{group}.pdf'
    logger.info(f"Writting dots into '{output_file}'.")

    c = canvas.Canvas(output_file, pagesize=landscape(config.page_size))
    c.setTitle(f'{group.title()}')
    center = get_word_centered_position(config, config.font_size)

    dot_size = config.font_size * 2
    max_dots_x = config.page_width // dot_size
    max_dots_y = config.page_height // dot_size

    with alive_bar(100) as bar:
        for dots_wanted in range(1, 101):
            c.setFillColor(config.font_color)
            dots = []
            attempt_number = 5
            while len(dots) < dots_wanted:
                attempt_number += 1
                reducer = int(attempt_number * config.font_size * 0.3)
                x_max = min(reducer, config.page_width // 2)
                y_max = min(reducer, config.page_height // 2)

                x, y = center
                x_span = random.randint(-1 * x_max, x_max)
                y_span = random.randint(-1 * y_max, y_max)
                position = x + x_span, y + y_span
                if outside_page(position, config) or overlaps_any(position, dots):
                    continue
                dots.append(position)
                c.circle(*position, config.font_size, stroke=0, fill=True)
                attempt_number = 5

            c.showPage()

            # c.setFont(config.font_name, config.font_size)
            # c.setFillColor(config.font_color)
            # c.drawCentredString(*center, str(len(dots)))
            # c.showPage()
            bar()


    c.save()


def distance_between_points(a, b):
    x_dist = a[0] - b[0]
    y_dist = a[1] - b[1]
    return math.sqrt((x_dist ** 2) + (y_dist ** 2))


def overlaps(a, b, min_distance=45):
    return distance_between_points(a, b) < min_distance


def overlaps_any(proposed_dot, dots):
    for dot in dots:
        if overlaps(dot, proposed_dot):
            return True
    return False


def outside_page(position, config):
    x, y = position
    safe_margin = config.font_size * 3.2
    return (
        x < safe_margin or
        y < safe_margin  or
        config.page_width - x < safe_margin or
        config.page_height - y < safe_margin
    )


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
        return sorted(words), None

    words_in_group = Counter(words)
    repeated_words = [word for word, count in words_in_group.items() if count > 1]
    words_in_group = set(words_in_group)
    new_words = words_in_group - already_seen_words
    ignored_words = words_in_group - new_words
    return sorted(new_words), set(repeated_words).union(ignored_words)


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
