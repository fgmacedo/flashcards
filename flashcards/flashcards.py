# coding: utf-8
import logging
from collections import Counter

logger = logging.getLogger(__name__)


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
