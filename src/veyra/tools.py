from __future__ import annotations
from dataclasses import dataclass
import os
from typing import Any
from openai import AsyncOpenAI
import logfire

from pydantic_ai import Agent, RunContext
from .agents import (
    briefing_agent,
    strategy_agent,
    image_prompt_agent,
    html_agent,
)
from .models import WorkflowStatus
from .persistence import PostgresStorage



@dataclass
class RunDependencies:
    """Dependencies needed for a tool execution."""
    thread_id: str
    storage: PostgresStorage
# The main agent that orchestrates the entire workflow.
orchestrator_agent = Agent(
    "openai:claude-sonnet-4-0",
    deps_type=RunDependencies,
    instructions="You are the project lead for AutoMarket. Your goal is to manage the process of creating a landing page from a conversation. Follow the steps logically: create a brief, then the strategy, then images, then the page, and finally publish it. Use your tools for each step and inform the user of your progress.",
)
@orchestrator_agent.tool
async def create_briefing(ctx: RunContext[RunDependencies]) -> str:
    """Analyzes the conversation transcript to create a structured marketing brief."""
    workflow = await ctx.deps.storage.get_workflow(ctx.deps.thread_id)
    if not workflow: return "Error: Workflow not found."

    result = await briefing_agent.run(workflow.conversation_transcript)
    workflow.briefing_md = result.output
    workflow.status = WorkflowStatus.BRIEFING_COMPLETE
    await ctx.deps.storage.update_workflow(workflow)

    logfire.info("Briefing created successfully for thread {thread_id}", thread_id=ctx.deps.thread_id)
    return "Briefing has been synthesized. The next step is to create the marketing strategy."

@orchestrator_agent.tool
async def create_strategy_and_plan(ctx: RunContext[RunDependencies]) -> str:
    """Develops a marketing strategy and a planning calendar based on the briefing."""
    workflow = await ctx.deps.storage.get_workflow(ctx.deps.thread_id)
    if not workflow or not workflow.briefing_md:
        return "Error: A briefing must be created before generating a strategy."

    result = await strategy_agent.run(workflow.briefing_md)
    workflow.strategy_and_plan_md = result.output
    workflow.status = WorkflowStatus.STRATEGY_COMPLETE
    await ctx.deps.storage.update_workflow(workflow)

    logfire.info("Strategy and plan created for thread {thread_id}", thread_id=ctx.deps.thread_id)
    return "Marketing strategy and planning calendar generated. Next, I will create images."

@orchestrator_agent.tool
async def create_images(ctx: RunContext[RunDependencies]) -> str:
    """Generates prompts for hero images and creates the images."""
    workflow = await ctx.deps.storage.get_workflow(ctx.deps.thread_id)
    if not workflow or not workflow.strategy_and_plan_md:
        return "Error: A marketing strategy is required to generate relevant images."

    prompt_result = await image_prompt_agent.run(workflow.strategy_and_plan_md)
    image_prompts = prompt_result.output

    # Use OpenAI client pointed at OpenRouter for image generation
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    
    image_urls = []
    for prompt in image_prompts:
        response = await client.images.generate(
            model="stabilityai/stable-diffusion-3", # Example model, check OpenRouter for availability
            prompt=prompt,
            n=1,
        )
        if response.data and response.data[0].url:
            image_urls.append(response.data[0].url)
    
    workflow.image_urls = image_urls
    workflow.status = WorkflowStatus.IMAGES_COMPLETE
    await ctx.deps.storage.update_workflow(workflow)

    logfire.info(f"Generated {len(image_urls)} images for thread {ctx.deps.thread_id}.")
    return f"{len(image_urls)} images created. The final step is to generate the landing page."

@orchestrator_agent.tool
async def create_landing_page(ctx: RunContext[RunDependencies]) -> str:
    """Generates the final HTML and Tailwind CSS for the landing page."""
    workflow = await ctx.deps.storage.get_workflow(ctx.deps.thread_id)
    if not workflow or not all([workflow.briefing_md, workflow.strategy_and_plan_md, workflow.image_urls]):
        return "Error: Briefing, strategy, and images are required to create the page."

    combined_context = f"""
    # Briefing
    {workflow.briefing_md}

    # Strategy and Plan
    {workflow.strategy_and_plan_md}

    # Image URLs
    {", ".join(workflow.image_urls)}
    """
    
    result = await html_agent.run(combined_context)
    workflow.html_content = result.output
    workflow.status = WorkflowStatus.HTML_COMPLETE
    await ctx.deps.storage.update_workflow(workflow)

    logfire.info("Landing page HTML generated for thread {thread_id}", thread_id=ctx.deps.thread_id)
    return "Landing page HTML has been generated. The final step is to publish it."

@orchestrator_agent.tool
async def publish_landing_page(ctx: RunContext[RunDependencies]) -> str:
    """Saves the generated HTML and returns a public URL to view it."""
    workflow = await ctx.deps.storage.get_workflow(ctx.deps.thread_id)
    if not workflow or not workflow.html_content:
        return "Error: HTML content must be generated before publishing."

    # In this setup, the page URL is based on the thread_id
    url_path = f"/pages/{ctx.deps.thread_id}"
    workflow.page_url = url_path
    workflow.status = WorkflowStatus.PUBLISHED
    await ctx.deps.storage.update_workflow(workflow)

    logfire.info(f"Landing page for thread {ctx.deps.thread_id} is live at {url_path}")
    return f"The landing page is now live! View it here: {url_path}"