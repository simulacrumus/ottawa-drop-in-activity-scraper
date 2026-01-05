# =============================================================================
#  Project:   City of Ottawa Drop-in Activity Scraper
#  File:      openai.py
#  Author:    Emrah Kinay
#  Created:   2026-01-04
#  License:   MIT
#
#  Description:
#      DeepSeek API Client
# =============================================================================

from openai import AsyncOpenAI

class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-nano",
        role: str = "user",
    ):
        self.api_key = api_key
        self.model = model
        self.role = role

        self.client = AsyncOpenAI(
            api_key=api_key
        )

    async def request(self, message: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": self.role,
                    "content": message,
                }
            ],
            stream=False,
        )
        return response.choices[0].message.content