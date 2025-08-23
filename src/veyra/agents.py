from textwrap import dedent
from pydantic_ai import Agent

# A specialized agent to synthesize a briefing from a conversation
briefing_agent = Agent(
    "openai:gpt-oss-120b",
    output_type=str,
    instructions="You are an expert project manager. Read the conversation transcript and distill it into a concise marketing briefing in Markdown format. Cover the product name, target audience, key features, and marketing tone.",
)

# A specialized agent to create a marketing strategy and plan
strategy_agent = Agent(
    "openai:gpt-oss-120b",
    output_type=str,
    instructions="You are a senior marketing strategist. Based on the provided briefing, create a high-level marketing strategy and a detailed 1-week planning calendar. Format the entire output as a single Markdown document.",
)

# A specialized agent to generate image prompts for an image model
image_prompt_agent = Agent(
    "openai:gpt-oss-120b",
    output_type=list[str],
    instructions="You are a creative director. Based on the marketing strategy, generate 3 distinct and detailed prompts for an AI image generator to create hero images for a landing page. The prompts should be visually descriptive, align with the marketing tone, and be suitable for a model like Stable Diffusion.",
)

# A specialized agent to generate the final landing page HTML
html_agent = Agent(
    "openai:gpt-5-mini",
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