from abc import ABC
from typing import Any, Tuple

import openai
import tiktoken

from llmpdf import db, util

COST_TABLE = {
    "gpt-4": {
        "input": 0.03 / 1000,
        "output": 0.06 / 1000,
    },
    "gpt-3.5-turbo": {
        "input": 0.0015 / 1000,
        "output": 0.002 / 1000,
    },
}


class AINode(ABC):
    def __init__(self, collection_name: str):
        self.settings = util.Settings()
        self.collection_name = collection_name
        self.database = db.Database()
        self.cost = 0.0

    def estimate_tokens(self) -> Tuple[int, int]:
        """Estimate the number of tokens in the input and output."""
        enc = tiktoken.encoding_for_model(self.settings.model)
        num_pages = self.database.count(self.collection_name)
        pages = self.database.list(self.collection_name, limit=num_pages)
        return (
            sum([len(enc.encode(page)) for page in pages]),
            self.settings.max_tokens,
        )

    def calculate_cost(self, response: Any = None) -> float:
        if response:
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
        else:
            input_tokens, output_tokens = self.estimate_tokens()

        input_cost = COST_TABLE[self.settings.model]["input"] * input_tokens
        output_cost = COST_TABLE[self.settings.model]["output"] * output_tokens
        return input_cost + output_cost


class Summarizer(AINode):
    """Summarizes text."""

    ZERO_SHOT_PROMPT = """
You are a diligent, precise, and concise summarizer. The following text has been selected from a PDF document. Summarize it in one paragraph.
Use only the provided text.

TEXT:
{text}
"""  # noqa: E501

    def zero_shot(self) -> Tuple[str, float]:
        """Summarize the text in one go."""
        text = "".join(self.database.list(self.collection_name))
        prompt = self.ZERO_SHOT_PROMPT.strip().format(text=text)

        openai.api_key = self.settings.openai_api_key
        response = openai.ChatCompletion.create(
            model=self.settings.model,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        cost = self.calculate_cost(response)
        return response.choices[0].message.content, cost  # type: ignore

    def summarize(self) -> Tuple[str, float]:
        """Summarize the text. Return the text and the cost."""
        input_tokens, _ = self.estimate_tokens()
        if input_tokens + self.settings.max_tokens < 8000:
            return self.zero_shot()

        return "This is a summary.", 0.0


class ChatBot(AINode):
    """Chat with your PDFs."""

    START_PROMPT = """
You are an assistant for question-answering tasks. I will provide you pages of a PDF file that you can use to answer your question.
Do not use prior information you may have about the topic.
If you do not know the answer, say that you do not know.

Use five sentences maximum and keep the answer concise.

Context:
{context}

Question:
{question}

Answer:
"""  # noqa: E501

    def __init__(self, collection_name: str):
        """Initialize the chatbot."""
        super().__init__(collection_name)
        self.memory = []

    def _messages(self, question: str, results: list[db.Result]):
        """Make the messages for the chatbot."""
        # Get context from the database
        context = "\n--\n".join(
            [f"Page {result.page}:\n{result.document}" for result in results]
        )
        prompt = self.START_PROMPT.strip().format(context=context, question=question)

        self.memory.append({"role": "user", "content": prompt})
        return self.memory

    def chat(self, question: str) -> Tuple[str, float]:
        """Chat with the database."""
        results = self.database.search(self.collection_name, question)
        if not results:
            return "I don't have anything in my database about this question.", 0.0

        openai.api_key = self.settings.openai_api_key
        response = openai.ChatCompletion.create(
            model=self.settings.model,
            messages=self._messages(question, results),
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
        )

        cost = self.calculate_cost(response)
        self.cost += cost
        return response.choices[0].message.content, cost  # type: ignore
