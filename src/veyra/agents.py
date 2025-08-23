import os

from datetime import datetime
from textwrap import dedent
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider


class CalendarPost(BaseModel):
    date: datetime
    title: str
    description: str


key = os.getenv("OPENROUTER_API_KEY")
if not key:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

provider = OpenRouterProvider(api_key=key)
writer_model = OpenAIModel(
    "google/gemini-2.5-flash",
    provider=provider,
)

coder_model = OpenAIModel(
    "google/gemini-2.5-flash",
    provider=provider,
)
# A specialized agent to synthesize a briefing from a conversation
briefing_agent = Agent(
    writer_model,
    output_type=str,
    instructions="You are an expert project manager. Read the conversation transcript and distill it into a concise marketing briefing in Markdown format. Cover the product name, target audience, key features, and marketing tone.",
)
# To prioritize Cerebras and allow fallback:


# A specialized agent to create a marketing strategy and plan
strategy_agent = Agent(
    writer_model,
    output_type=str,
    instructions="You are a senior marketing strategist. Based on the provided briefing, create a high-level marketing strategy. Format the entire output as a single Markdown document.",
)

calendar_agent = Agent(
    writer_model,
    output_type=list[CalendarPost],
    instructions="You are a senior marketing strategist. Create a detailed 1-month planning calendar for posts in social media",
)

# A specialized agent to generate image prompts for an image model
image_prompt_agent = Agent(
    writer_model,
    output_type=list[str],
    instructions="You are a creative director. Based on the marketing strategy, generate social media 1 post using html and tailwind css.",
)

# A specialized agent to generate the final landing page HTML
html_agent = Agent(
    coder_model,
    output_type=str,
    instructions=dedent("""
        You are an expert web developer specializing in high-converting landing pages.
        Generate a single, complete HTML file using Tailwind CSS for styling.

        - Use the provided briefing, strategy, and image URLs to populate the content.
        - Create sections for a hero banner, key features, and a call-to-action.
        - Ensure the final output is a single block of valid HTML code, starting with `<!DOCTYPE html>` and ending with `<:html>`.
        - Do not include any markdown formatting like ```html in your response.
    """),
)
