#! /usr/bin/env python3
import time
import json
import argparse
import traceback
from collections import OrderedDict
from people_also_ask.google import get_related_questions
from people_also_ask.exceptions import (
    InvalidQuestionInputFileError,
    FailedToWriteOuputFileError,
)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input-file", "-i", help="input file which is a txt file containing list of questions", required=True)
    parser.add_argument("--output-file", "-o", help="output file which is .json file containing a dictionnary of question: answer", required=True)

    return parser.parse_args()

def read_questions(input_file):
    try:
        with open(input_file, "r") as fd:
            text = fd.read()
            return OrderedDict.fromkeys(text.strip().split("\n")).keys()
    except Exception:
        message = traceback.format_exc()
        raise InvalidQuestionInputFileError(input_file, message)

def write_question_answers(output_file, data):
    try:
        with open(output_file, "w") as fd:
            fd.write(json.dumps(data))
    except Exception:
        message = traceback.format_exc()
        raise FailedToWriteOuputFileError(output_file, message)

def collect_data(input_file, output_file):
    questions = read_questions(input_file)
    data = {}

    counter = 0

    start_time = time.time()
    for question in questions:
        counter += 1
        print(f"COLLECTING {counter}/{len(questions)}")
        data[question] = get_related_questions(question, 100)
    collect_time = (time.time() - start_time) / 60  #  minutes

    print(f"Collected answers for {len(questions)} questions in {collect_time} minutes")
    write_question_answers(output_file, data)

def main():
    args = parse_args()
    collect_data(args.input_file, args.output_file)

if __name__ == "__main__":
    main()
