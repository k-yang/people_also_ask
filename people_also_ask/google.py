#! /usr/bin/env python3
import sys
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Generator
import time
import requests
import random

from people_also_ask.parser import (
    extract_related_questions,
    get_featured_snippet_parser,
)
from people_also_ask.exceptions import (
    RelatedQuestionParserError,
    FeaturedSnippetParserError,
)
from people_also_ask.request import get

URL = "https://www.google.com/search"


def search(keyword: str) -> Optional[BeautifulSoup]:
    """return html parser of google search result"""
    time.sleep(1)
    params = {
        "q": keyword,
        "oq": keyword,
        # "gl": "us",
        "aqs": "chrome.0.35i39j46i131i433i512j69i57j0i512l7.2306j0j7",
        "sourceid": "chrome",
        "ie": "UTF-8",
    }
    headers = {
        # "accept-language": "en-US,en;q=0.9",
        # "accept-encoding": "gzip, deflate, br",
        # "cache-control": "max-age=0",
        # "sec-fetch-dest": "document",
        # "sec-fetch-mode": "navigate",
        # "sec-fetch-site": "same-origin",
        # "sec-fetch-user": "?1",
        # "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    }
    r = requests.Session().get(
        URL,
        params=params,
        headers=headers,
    )

    document = BeautifulSoup(r.text, "html.parser")

    return document


def _get_related_questions(text: str) -> Dict[str, str]:
    """Gets related questions from google search result

    Args:
        text (str): _description_

    Returns:
        Dict[str, str]: _description_
    """
    document = search(text)
    return extract_related_questions(document)


def generate_related_questions(questions: str) -> Generator[List[str], None, None]:
    """
    generate the questions related to text,
    these questions are found recursively

    :param str text: text to search
    """
    searched_questions = set(questions)
    questions = set(_get_related_questions(questions))
    while questions:
        questions = questions.pop()
        yield questions
        searched_questions.add(questions)
        questions |= set(_get_related_questions(questions))
        questions -= searched_questions


def get_related_questions(
    seed_question: str, max_related_questions: int = 4
) -> Dict[str, str]:
    """Returns related questions to the seed question

    Args:
        seed_question (str): _description_
        max_related_questions (int, optional): _description_. Defaults to 4.

    Returns:
        Dict[str, str]: _description_
    """

    print("asking question: ", seed_question)
    related_questions = _get_related_questions(seed_question)
    while len(related_questions.keys()) < max_related_questions:
        print(len(related_questions))
        next_question = random.choice(list(related_questions.keys()))
        print("asking question: ", next_question)
        new_related_questions = _get_related_questions(next_question)
        related_questions = {**related_questions, **new_related_questions}

    return related_questions


def get_answer(question: str) -> Dict[str, Any]:
    """
    return a dictionary as answer for a question.

    :param str question: asked question
    """
    document = search(question)
    related_questions = extract_related_questions(document)
    featured_snippet = get_featured_snippet_parser(question, document)
    if not featured_snippet:
        res = dict(
            has_answer=False,
            question=question,
            related_questions=related_questions,
        )
    else:
        res = dict(
            has_answer=True,
            question=question,
            related_questions=related_questions,
        )
        try:
            res.update(featured_snippet.to_dict())
        except Exception:
            raise FeaturedSnippetParserError(question)
    return res


def generate_answer(text: str) -> Generator[dict, None, None]:
    """
    generate answers of questions related to text

    :param str text: text to search
    """
    answer = get_answer(text)
    questions = set(answer["related_questions"])
    searched_text = set(text)
    if answer["has_answer"]:
        yield answer
    while questions:
        text = questions.pop()
        answer = get_answer(text)
        if answer["has_answer"]:
            yield answer
        searched_text.add(text)
        questions |= set(get_answer(text)["related_questions"])
        questions -= searched_text


def get_simple_answer(question: str, depth: bool = False) -> str:
    """
    return a text as summary answer for the question

    :param str question: asked question
    :param bool depth: return the answer of first related question
        if no answer found for question
    """
    document = search(question)
    featured_snippet = get_featured_snippet_parser(question, document)
    if featured_snippet:
        return featured_snippet.response
    if depth:
        related_questions = get_related_questions(question)
        if not related_questions:
            return ""
        return get_simple_answer(related_questions[0])
    return ""


if __name__ == "__main__":
    from pprint import pprint as print

    print(get_answer(sys.argv[1]))
