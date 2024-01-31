import abc
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

UNDERSCORE_MARKER = "_______"


def set_uniform_underscore_length(text: str) -> str:
    return re.sub(r"_{2,}", UNDERSCORE_MARKER, text)


def tex_escape(text: str) -> str:
    # https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates
    conv = {
        UNDERSCORE_MARKER: r"\underline{\hspace{1cm}}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\^{}",
        "\\": r"\textbackslash{}",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }

    regex = re.compile(
        "|".join(
            re.escape(str(key))
            for key in sorted(conv.keys(), key=lambda item: -len(item))
        )
    )
    return regex.sub(lambda match: conv[match.group()], text)


class Section(str, Enum):
    READING = "READING"
    WRITING = "WRITING"
    RHETORIC = "RHETORIC"


class QuestionType(str, Enum):
    # Reading types:
    WORDS_IN_CONTEXT = "WORDS_IN_CONTEXT"
    STRUCTURE_PURPOSE = "STRUCTURE_PURPOSE"
    CROSS_TEXT = "CROSS_TEXT"
    CENTRAL_IDEA = "CENTRAL_IDEA"
    QUANTITATIVE_EVIDENCE = "QUANTITATIVE_EVIDENCE"
    TEXTUAL_EVIDENCE = "TEXTUAL_EVIDENCE"
    INFERENCES = "INFERENCES"

    # Writing types:
    NUMBER_TENSE_AGREEMENT = "NUMBER_TENSE_AGREEMENT"
    PUNCTUATION = "PUNCTUATION"
    SENTENCE_STRUCTURE = "SENTENCE_STRUCTURE"
    TRANSITIONS = "TRANSITIONS"
    # Rhetoric:
    RHETORICAL_ANALYSIS = "RHETORICAL_ANALYSIS"


class AnswerChoice(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"

    def to_string(self):
        return self.value


@dataclass
class Solution:
    choice: AnswerChoice
    explanation: str


class Prompt(abc.ABC):
    # @classmethod
    # @abc.abstractmethod
    # def from_json(cls, json: dict) -> "Prompt":
    ...


@dataclass
class BasicPrompt(Prompt):
    text: str
    question: str


@dataclass
class ExercptPrompt(Prompt):
    pretext: str

    text: str
    question: str


@dataclass
class RhetoricalAnalysisPrompt(Prompt):
    pretext: str
    notes: list[str | list[str]]
    question: str


@dataclass
class FigurePrompt(Prompt):
    figure: Path
    text: str
    question: str


@dataclass
class CrossTextPrompt(Prompt):
    question: str
    pretext: str
    text1: str
    text2: str


QUESTION_TO_PROMPT_TYPE_MAPPING = {
    QuestionType.WORDS_IN_CONTEXT: ExercptPrompt,
    QuestionType.STRUCTURE_PURPOSE: ExercptPrompt,
    QuestionType.CROSS_TEXT: CrossTextPrompt,
    QuestionType.CENTRAL_IDEA: ExercptPrompt,
    QuestionType.QUANTITATIVE_EVIDENCE: FigurePrompt,
    QuestionType.TEXTUAL_EVIDENCE: BasicPrompt,
    QuestionType.INFERENCES: BasicPrompt,
    QuestionType.NUMBER_TENSE_AGREEMENT: BasicPrompt,
    QuestionType.PUNCTUATION: BasicPrompt,
    QuestionType.SENTENCE_STRUCTURE: BasicPrompt,
    QuestionType.TRANSITIONS: BasicPrompt,
    QuestionType.RHETORICAL_ANALYSIS: RhetoricalAnalysisPrompt,
}


@dataclass
class SATQuestion:
    source: str
    section: Section
    type: QuestionType
    number: int
    prompt: Prompt
    choices: list[str]
    solution: Solution

    @property
    def identifier(self) -> str:
        src = self.source.upper()[0]
        section = self.section.value.upper()[0]
        # type_ = "".join(word[0].upper() for word in self.type.value.split("_"))
        type_ = self.type.value.replace("_", "-")
        return f"{src}.{section}.{type_}.{self.number:03}"

    @classmethod
    def from_directory(cls, directory: Path) -> list["SATQuestion"]:
        questions = []
        for filename in directory.iterdir():
            if filename.suffix == ".json":
                questions.extend(cls.from_file(filename))
        return questions

    @classmethod
    def from_file(cls, filename: Path) -> list["SATQuestion"]:
        with open(filename, "r") as f:
            data = json.load(f)

        return [cls.from_json(question) for question in data]

    @classmethod
    def from_json(cls, json: dict) -> "SATQuestion":
        question_type = QuestionType(json["type"])
        prompt_type = QUESTION_TO_PROMPT_TYPE_MAPPING[question_type]
        try:
            prompt = prompt_type(**json["prompt"])
        except TypeError:
            raise TypeError(
                f"Prompt type {prompt_type} does not match JSON data {json['prompt']}"
            )
        return cls(
            source="Barron's SAT 2024",
            section=Section(json["section"]),
            type=QuestionType(json["type"]),
            number=json["number"],
            prompt=prompt,
            choices=json["choices"],
            solution=Solution(
                choice=AnswerChoice(json["solution"]["choice"]),
                explanation=json["solution"]["explanation"],
            ),
        )
