import os
from openai import OpenAI
import sys

class OpenAIClientError(Exception):
    """Custom exception for OpenAI client errors."""
    pass

class OpenAIClient:
    def __init__(self, api_key=None):
        """
        Initialize the OpenAI API client.
        :param api_key: API key as a string. If not provided, will be read from the OPENAI_API_KEY environment variable.
        """
        
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise OpenAIClientError("OPENAI_API_KEY is not set in environment variables.")
        # openai.api_key = self.api_key
        self.client = OpenAI(api_key=api_key)


    def query(self, message, model="o3-mini", **kwargs):
        """
        Query the OpenAI API with a given message.
        :param message: The prompt message to send.
        :param model: The model to use (default: "o3-mini"). You can add more models later.
        :param kwargs: Additional keyword arguments for the API call.
        :return: The response message content as a string.
        """
        try:
            # response = openai.ChatCompletion.create(
            #     model=model,
            #     messages=[{"role": "user", "content": message}],
            #     **kwargs,
            # )
            
            response = self.client.chat.completions.create(
                model="gpt-4",  # or "gpt-4" if you have access
                messages=[
                    {"role": "user", "content": message}
                ]
            )

            # Return the content of the first response message.
            return response.choices[0].message.content
        except Exception as e:
            raise OpenAIClientError(f"Failed to query OpenAI API: {e}") from e
