# =============================================================================
#  Project:   City of Ottawa Drop-in Activity Scraper
#  File:      deepseek.py
#  Author:    Emrah Kinay
#  Created:   2025-09-12
#  License:   MIT
#
#  Description:
#      DeepSeek API Client
# =============================================================================

from openai import AsyncOpenAI

class DeepSeekClient:
    def __init__(
        self,
        api_key:str,
        base_url:str = "https://api.deepseek.com",
        model:str = "deepseek-chat",
        role:str = "user"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.role = role

        self.client = AsyncOpenAI(
            api_key = api_key, 
            base_url = base_url
        )

    async def request(self, message: str)->str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": self.role, 
                    "content": message
                },
            ],
            stream=False
        )
        return response.choices[0].message.content