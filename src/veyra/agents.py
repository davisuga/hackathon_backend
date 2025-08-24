import os

from textwrap import dedent
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from .models import CalendarPost


key = os.getenv("OPENROUTER_API_KEY")
if not key:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

provider = OpenRouterProvider(api_key=key)
writer_model = OpenAIModel(
    "google/gemini-2.5-flash",
    provider=provider,
)

coder_model = OpenAIModel(
    "openai/gpt-5",
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
    instructions="""

    You are a senior marketing strategist. Create a detailed 1-month content calendar for posts in instagram. you need to specify if it is for feed, story, or post.
    type,resolution
    feed,1200x900
    story,1080x1920
    post,1080x1080
    """,
)


# A specialized agent to generate image prompts for an image model
image_prompt_agent = Agent(
    writer_model,
    output_type=str,
    instructions="""
    Inspired by this example:
    <example>
## 🌿 *Prompt SORA – Instagram Feed (4:3)*

You are a senior wellness-focused visual designer creating a hero banner background for a clean supplement brand like PuraFit. This visual must accompany the following page content:
Headline: Nature's Golden Anti-Inflammatory
Subheadline: Ancient wisdom meets modern science — clinically proven for wellness 🎯

🖼 *Scene Concept (4:3)*
A real man (age 40–55) standing in a warm, naturally lit herbal garden or backyard wellness space during early morning or golden hour. The man is casually dressed in neutral linen or cotton (cream, soft olive, or beige), gently tending to turmeric plants, herbs, or simply enjoying the natural surroundings with mindful presence. He may be sipping a mug of golden turmeric tea or lightly touching a flowering turmeric leaf.

📐 *Composition & Format (Feed 4:3)*

•⁠  ⁠Framing adapted to 4:3 ratio for Instagram feed.
•⁠  ⁠Subject slightly off-center with negative space beside him for balance.
•⁠  ⁠Soft depth of field: blurred background, crisp subject focus.
•⁠  ⁠Natural framing with lush greenery and turmeric flowers.

🎨 *Color Palette (PuraFit)*

•⁠  ⁠Background neutrals: #F4F2EF
•⁠  ⁠Golden turmeric tones: #D4A574, #B8703F
•⁠  ⁠Wardrobe & props neutrals: #FAF9F5, #F4EBDC
•⁠  ⁠Leafy greens: desaturated olive or sage tones

✍ *Emotion & Story*
A quiet, grounded moment of wellness. Empowered health through nature, expressed with editorial minimalism.

---

## 🌿 *Prompt SORA – Instagram Stories (9:16)*

You are a senior wellness-focused visual designer creating a hero background visual for a clean supplement brand like PuraFit. This visual must accompany the following page content:
Headline: Nature's Golden Anti-Inflammatory
Subheadline: Ancient wisdom meets modern science — clinically proven for wellness 🎯

🖼 *Scene Concept (9:16)*
A real man (age 40–55) in a vertical frame, standing in a warm, naturally lit herbal garden or backyard wellness space during golden hour. The man wears neutral linen or cotton (cream, soft olive, beige), holding a mug of golden turmeric tea or gently tending to turmeric plants. He is centered but with vertical breathing space above and below to allow headline and subheadline overlay.

📐 *Composition & Format (Stories 9:16)*

•⁠  ⁠Tall vertical framing optimized for Instagram Stories.
•⁠  ⁠Subject centered or slightly lower, with clear open space above for text.
•⁠  ⁠Soft natural depth of field: foreground details crisp, background blurred.
•⁠  ⁠Garden textures and golden sunlight emphasized in top half of frame.

🎨 *Color Palette (PuraFit)*

•⁠  ⁠Background neutrals: #F4F2EF
•⁠  ⁠Golden turmeric tones: #D4A574, #B8703F
•⁠  ⁠Wardrobe & props neutrals: #FAF9F5, #F4EBDC
•⁠  ⁠Leafy greens: desaturated olive or sage tones

✍ *Emotion & Story*
Not a staged ad, but a serene morning ritual captured authentically. A glimpse of empowered health and harmony through turmeric and nature.

---

## 🌿 *Prompt SORA – Instagram Post Fijo (1:1)*

You are a senior wellness-focused visual designer creating a square hero background for a clean supplement brand like PuraFit. This visual must accompany the following page content:
Headline: Nature's Golden Anti-Inflammatory
Subheadline: Ancient wisdom meets modern science — clinically proven for wellness 🎯

🖼 *Scene Concept (1:1)*
A real man (age 40–55) in a warm, naturally lit herbal garden or backyard wellness space during golden hour. The man is casually dressed in neutral linen or cotton (cream, soft olive, beige), gently tending to turmeric plants, herbs, or sipping a mug of golden turmeric tea. He should appear calm, grounded, and authentic, framed in a way that balances him within a square composition.

📐 *Composition & Format (Post 1:1)*

•⁠  ⁠Perfect square framing for Instagram grid.
•⁠  ⁠Man placed slightly off-center with balanced surrounding elements.
•⁠  ⁠Depth of field: sharp subject, softly blurred herbal background.
•⁠  ⁠Equal emphasis on subject and lush turmeric/herbal environment.

🎨 *Color Palette (PuraFit)*

•⁠  ⁠Background neutrals: #F4F2EF
•⁠  ⁠Golden turmeric tones: #D4A574, #B8703F
•⁠  ⁠Wardrobe & props neutrals: #FAF9F5, #F4EBDC
•⁠  ⁠Leafy greens: desaturated olive or sage tones

✍ *Emotion & Story*
A trustworthy, editorial-style moment of morning wellness. Natural, minimalistic, and aligned with PuraFit’s balance of science and nature.

</example>
    You are a prompt engineer. Generate 1 prompt for an image model based on user briefing. The goal is to create an image for a social media post. It must be generic to any post from that brand""",
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
