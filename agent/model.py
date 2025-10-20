from __future__ import annotations
import openai
import os
import sys
import logging
import random
import time
from typing import Any, Callable, Optional, Type
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model hyper-parameters.
MAX_TOKENS: int = 2000
NUM_SAMPLES: int = 1
TEMPERATURE: float = 0.4

class LLM:
    """Base LLM."""
    # Should be set by the subclass.
    name: str
    # TODO(mihaimaruseac): Should this be MAX_TOKENS or a different global?
    context_window: int = 2000  # Default token size.

    MAX_INPUT_TOKEN: int = sys.maxsize

    _max_attempts = 5  # Maximum number of attempts to get prediction response

    def __init__(
        self,
        ai_binary: str,
        max_tokens: int = MAX_TOKENS,
        num_samples: int = NUM_SAMPLES,
        temperature: float = TEMPERATURE,
        temperature_list: Optional[list[float]] = None,
    ):
        self.ai_binary = ai_binary

        # Model parameters.
        self.max_tokens = max_tokens
        self.num_samples = num_samples
        self.temperature = temperature
        self.temperature_list = temperature_list
    
    @classmethod
    def setup(
        cls,
        ai_binary: str,
        name: str,
        max_tokens: int = MAX_TOKENS,
        num_samples: int = NUM_SAMPLES,
        temperature: float = TEMPERATURE,
        temperature_list: Optional[list[float]] = None,
    ):
        """Prepares the LLM for fuzz target generation."""
        for subcls in cls.all_llm_subclasses():
            if getattr(subcls, 'name', None) == name:
                return subcls(
                    ai_binary,
                    max_tokens,
                    num_samples,
                    temperature,
                    temperature_list,
                )

        raise ValueError(f'Bad model type {name}')

    @classmethod
    def all_llm_subclasses(cls):
        """All subclasses."""
        yield cls
        for subcls in cls.__subclasses__():
            yield from subcls.all_llm_subclasses()

    def _is_retryable_error(self, err: Exception,
                            api_errors: list[Type[Exception]],
                            tb: traceback.StackSummary) -> bool:
        """Validates if |err| is worth retrying."""
        if any(isinstance(err, api_error) for api_error in api_errors):
            return True

        # A known case from vertex package, no content due to mismatch roles.
        if (isinstance(err, ValueError) and
            'Content roles do not match' in str(err) and tb[-1].filename.endswith(
                'vertexai/generative_models/_generative_models.py')):
            return True

        # A known case from vertex package, content blocked by safety filters.
        if (isinstance(err, ValueError) and
            'blocked by the safety filters' in str(err) and
            tb[-1].filename.endswith(
                'vertexai/generative_models/_generative_models.py')):
            return True
        return False
    
    def _delay_for_retry(self, attempt_count: int) -> None:
        """Sleeps for a while based on the |attempt_count|."""
        # Exponentially increase from 5 to 80 seconds + some random to jitter.
        delay = 5 * 2**attempt_count + random.randint(1, 5)
        logging.warning('Retry in %d seconds...', delay)
        time.sleep(delay)

    def _save_output(self, index: int, content: str, response_dir: str) -> None:
        """Saves the raw |content| from the model ouput."""
        sample_id = index + 1
        raw_output_path = os.path.join(response_dir, f'{sample_id:02}.rawoutput')
        with open(raw_output_path, 'w+') as output_file:
            output_file.write(content)

    def with_retry_on_error(self, func: Callable, api_errs: list[Type[Exception]]) -> Any:
        """
        Retry when the function returns an expected error with exponential backoff.
        """
        for attempt in range(1, self._max_attempts + 1):
            try:
                return func()
            except Exception as err:
                logging.warning('LLM API Error when responding (attempt %d): %s',
                                attempt, err)
                tb = traceback.extract_tb(err.__traceback__)
                if (not self._is_retryable_error(err, api_errs, tb) or
                    attempt == self._max_attempts):
                    logging.warning(
                        'LLM API cannot fix error when responding (attempt %d) %s: %s',
                        attempt, err, traceback.format_exc())
                    raise err
            self._delay_for_retry(attempt_count=attempt)
        return None


class OpenAIClientError(Exception):
    """Custom exception for OpenAI client errors."""
    pass

class GPT(LLM):
    """OpenAI's GPT model encapsulator."""

    # name = 'gpt-3.5-turbo'
    name = "gpt-4.1"

    def _get_client(self):
        """Returns the OpenAI client."""
        try:
            return openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        except Exception as e:
            raise OpenAIClientError(f"Failed to query OpenAI API: {e}") from e
    
    # ============================== Generation ============================== #
    def query_llm(self, prompt: str, response_dir=None, log=False) -> None:
        """Queries OpenAI's API and stores response in |response_dir|."""
        if self.ai_binary:
            raise ValueError(f'OpenAI does not use local AI binary: {self.ai_binary}')
        if self.temperature_list:
            logger.info('OpenAI does not allow temperature list: %s',
                    self.temperature_list)

        client = self._get_client()

        completion = self.with_retry_on_error(
            lambda: client.chat.completions.create(messages=prompt,
                                                model=self.name,
                                                n=self.num_samples,
                                                temperature=self.temperature),
            [openai.OpenAIError])
        for index, choice in enumerate(completion.choices):  # type: ignore
            content = choice.message.content
            if log:
                logger.info(f'LLM output: {content}')
        if response_dir == None:
            logger.info('response_dir empty, not saving output to a file yet')
            return completion, content
        self._save_output(index, content, response_dir)
        return completion

class GPT4o(LLM):
    """OpenAI's GPT model encapsulator."""

    name = "gpt-4o"

    def _get_client(self):
        """Returns the OpenAI client."""
        try:
            return openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        except Exception as e:
            raise OpenAIClientError(f"Failed to query OpenAI API: {e}") from e
    
    # ============================== Generation ============================== #
    def query_llm(self, prompt: str, response_dir=None, log=False) -> None:
        """Queries OpenAI's API and stores response in |response_dir|."""
        if self.ai_binary:
            raise ValueError(f'OpenAI does not use local AI binary: {self.ai_binary}')
        if self.temperature_list:
            logger.info('OpenAI does not allow temperature list: %s',
                    self.temperature_list)

        client = self._get_client()

        completion = self.with_retry_on_error(
            lambda: client.chat.completions.create(messages=prompt,
                                                model=self.name,
                                                n=self.num_samples,
                                                temperature=self.temperature),
            [openai.OpenAIError])
        for index, choice in enumerate(completion.choices):  # type: ignore
            content = choice.message.content
            if log:
                logger.info(f'LLM output: {content}')
        if response_dir == None:
            logger.info('response_dir empty, not saving output to a file yet')
            return completion, content
        self._save_output(index, content, response_dir)
        return completion