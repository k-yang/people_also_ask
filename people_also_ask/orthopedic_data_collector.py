#! /usr/bin/env python3
import time
import json
import argparse
import traceback
from collections import OrderedDict
from people_also_ask.google import get_related_questions
from people_also_ask.exceptions import (
    InvalidQuestionInputFileError,
)
from typing import Dict
import csv


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input-file",
        "-i",
        help="input file which is a txt file containing list of questions",
        required=True,
    )
    parser.add_argument(
        "--num-questions",
        "-n",
        help="number of related questions to scrape",
        required=True,
        default=4,
    )

    return parser.parse_args()


def read_questions(input_file: str):
    """Reads seed questions from a file and returns a list of questions

    Args:
        input_file (_type_): _description_

    Raises:
        InvalidQuestionInputFileError: _description_

    Returns:
        _type_: _description_
    """
    try:
        with open(input_file, "r") as fd:
            text = fd.read()
            return OrderedDict.fromkeys(text.strip().split("\n")).keys()
    except Exception:
        message = traceback.format_exc()
        raise InvalidQuestionInputFileError(input_file, message)


def write_related_questions(data: Dict[str, Dict[str, str]]):
    """Writes the data to a json file

    Args:
        output_file (_type_): _description_
        data (_type_): _description_

    """
    for seed_question, related_questions in data.items():
        with open(f"{seed_question}.csv", "w", newline="") as fd:
            writer = csv.writer(fd)
            for question, link in related_questions.items():
                writer.writerow([question, link])


def collect_data(input_file: str, num_questions: int):
    questions = read_questions(input_file)
    data: Dict[str, Dict[str, str]] = {}

    counter = 0

    start_time = time.time()
    for question in questions:
        counter += 1
        print(f"COLLECTING {counter}/{len(questions)}")
        data[question] = get_related_questions(question, num_questions)
    collect_time = time.time() - start_time  #  minutes

    print(f"Collected answers for {len(questions)} questions in {collect_time} seconds")
    write_related_questions(data)


def main():
    args = parse_args()
    collect_data(args.input_file, int(args.num_questions))


if __name__ == "__main__":
    main()
