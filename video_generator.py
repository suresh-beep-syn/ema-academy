import json
import os
import re
import math
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips

# ==========================================
# EMA 2070 - QUESTION VIDEO GENERATOR
# ==========================================

WIDTH = 1920
HEIGHT = 1080

BG_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)

FONT_SIZE = 48
QUESTION_SIZE = 54
HEADER_SIZE = 38

# Minimum slide durations (seconds)
QUESTION_MIN_TIME = 6
OPTIONS_MIN_TIME = 7
ANSWER_MIN_TIME = 5
EXPLANATION_MIN_TIME = 10

# Reading speed
WORDS_PER_SECOND = 3.0

INPUT_FILE = "questions.json"
OUTPUT_FILE = "EMA_Question_Video.mp4"


# ==========================================
# FONT
# ==========================================

def load_font(size):
    possible_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf"
    ]

    for font_path in possible_fonts:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)

    return ImageFont.load_default()


FONT = load_font(FONT_SIZE)
QUESTION_FONT = load_font(QUESTION_SIZE)
HEADER_FONT = load_font(HEADER_SIZE)


# ==========================================
# AUTOMATIC READING TIME
# ==========================================

def reading_time(text, minimum):
    words = len(str(text).split())
    calculated = math.ceil(words / WORDS_PER_SECOND)
    return max(minimum, calculated + 2)


# ==========================================
# TEXT WRAPPING
# ==========================================

def wrap_text(text, font, max_width):
    text = str(text)
    lines = []

    for paragraph in text.split("\n"):
        words = paragraph.split()
        current_line = ""

        for word in words:
            test_line = word if not current_line else current_line + " " + word

            bbox = font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

    return lines


# ==========================================
# CREATE SLIDE
# ==========================================

def create_slide(title, content, font=FONT):

    image = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)

    margin_left = 110
    margin_right = 110
    max_width = WIDTH - margin_left - margin_right

    # Header
    draw.text(
        (margin_left, 55),
        "EMA 2070 | ELITE MATHS ACADEMY",
        font=HEADER_FONT,
        fill=TEXT_COLOR
    )

    # Divider
    draw.line(
        (margin_left, 115, WIDTH - margin_right, 115),
        fill=(120, 120, 120),
        width=2
    )

    # Title
    draw.text(
        (margin_left, 160),
        title,
        font=QUESTION_FONT,
        fill=TEXT_COLOR
    )

    # Content
    lines = wrap_text(content, font, max_width)

    y = 270
    line_spacing = 24

    for line in lines:
        draw.text(
            (margin_left, y),
            line,
            font=font,
            fill=TEXT_COLOR
        )

        bbox = draw.textbbox((margin_left, y), line, font=font)
        line_height = bbox[3] - bbox[1]

        y += line_height + line_spacing

    return image


# ==========================================
# VIDEO SLIDE HELPER
# ==========================================

clips = []

def add_slide(title, content, minimum_time, font=FONT):

    image = create_slide(title, content, font)

    duration = reading_time(content, minimum_time)

    clip = ImageClip(image).with_duration(duration)

    clips.append(clip)


# ==========================================
# LOAD QUESTIONS
# ==========================================

def load_questions():

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        questions = data

    elif isinstance(data, dict):
        questions = data.get("questions", [])

    else:
        questions = []

    if not questions:
        raise ValueError("No questions found in questions.json")

    return questions


# ==========================================
# ANSWER FORMAT
# ==========================================

def get_correct_answer(question, options):

    answer = question.get("answer", question.get("correct_answer"))

    if answer is None:
        return "Correct answer not provided."

    # If answer is an integer index
    if isinstance(answer, int):
        if 0 <= answer < len(options):
            return options[answer]

        if 1 <= answer <= len(options):
            return options[answer - 1]

    # If answer is a letter such as A, B, C, D
    if isinstance(answer, str):
        letter = answer.strip().upper()

        if letter in ["A", "B", "C", "D"]:
            index = ord(letter) - ord("A")

            if index < len(options):
                return options[index]

    return str(answer)


# ==========================================
# BUILD VIDEO
# ==========================================

def build_video():

    questions = load_questions()

    for number, question_data in enumerate(questions, start=1):

        question_text = question_data.get(
            "question",
            question_data.get("q", "")
        )

        options = question_data.get("options", [])

        answer = get_correct_answer(question_data, options)

        explanation = question_data.get(
            "explanation",
            question_data.get("solution", "Explanation not provided.")
        )

        # ----------------------------------
        # QUESTION SLIDE
        # ----------------------------------

        add_slide(
            f"QUESTION {number}",
            question_text,
            QUESTION_MIN_TIME,
            QUESTION_FONT
        )

        # ----------------------------------
        # OPTIONS SLIDE
        # ----------------------------------

        if options:

            option_text = "\n\n".join(
                f"{chr(65 + i)}. {option}"
                for i, option in enumerate(options)
            )

            add_slide(
                "OPTIONS",
                option_text,
                OPTIONS_MIN_TIME
            )

        # ----------------------------------
        # ANSWER SLIDE
        # ----------------------------------

        add_slide(
            "CORRECT ANSWER",
            answer,
            ANSWER_MIN_TIME
        )

        # ----------------------------------
        # EXPLANATION SLIDE
        # ----------------------------------

        add_slide(
            "EXPLANATION",
            explanation,
            EXPLANATION_MIN_TIME
        )

    # ======================================
    # FINAL VIDEO
    # ======================================

    final_video = concatenate_videoclips(
        clips,
        method="compose"
    )

    final_video.write_videofile(
        OUTPUT_FILE,
        fps=24,
        codec="libx264",
        audio=False
    )

    print("\nVIDEO CREATED SUCCESSFULLY!")
    print("Output file:", OUTPUT_FILE)


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":
    build_video()
