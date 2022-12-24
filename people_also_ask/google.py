#! /usr/bin/env python3
import sys
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Generator
import time

from people_also_ask.parser import (
    extract_related_questions,
    get_featured_snippet_parser,
)
from people_also_ask.exceptions import (
    RelatedQuestionParserError,
    FeaturedSnippetParserError
)
from people_also_ask.request import get

URL = "https://www.google.com/search"

def search(keyword: str) -> Optional[BeautifulSoup]:
    """return html parser of google search result"""
    time.sleep(1)
    params = {"q": keyword, "gl": "us"}
    response = get(URL, params=params)
    return BeautifulSoup(response.text, "html.parser")


def _get_related_questions(text: str) -> List[str]:
    """
    return a list of questions related to text.
    These questions are from search result of text

    :param str text: text to search
    """
    document = search(text)
    if not document:
        return []
    try:
        return extract_related_questions(document)
    except Exception:
        raise RelatedQuestionParserError(text)


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


def get_related_questions(seed_question: str, max_related_questions: Optional[int] = None):
    """
    return a number of questions related to text.
    These questions are found recursively.

    :param str text: text to search
    """
    if max_related_questions is None:
        return _get_related_questions(seed_question)

    questions = set(_get_related_questions(seed_question))
    related_questions = set(questions)

    while len(related_questions) < max_related_questions:
        next_question = questions.pop()
        print(next_question)
        questions |= set(_get_related_questions(next_question))
        related_questions |= questions
        print(len(related_questions))
    return list(related_questions)


def get_answer(question: str) -> Dict[str, Any]:
    """
    return a dictionary as answer for a question.

    :param str question: asked question
    """
    document = search(question)
    related_questions = extract_related_questions(document)
    featured_snippet = get_featured_snippet_parser(
            question, document)
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
    featured_snippet = get_featured_snippet_parser(
            question, document)
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
