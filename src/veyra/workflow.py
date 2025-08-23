from typing import Any, Awaitable, Callable

import logfire
from fastapi import HTTPException
from pydantic import TypeAdapter

from .models import AutoMarketState, WorkflowStatus
from .agents import (
    CalendarPost,
    briefing_agent,
    strategy_agent,
    image_prompt_agent,
    html_agent,
    calendar_agent,
)
from .persistence import PostgresStorage

from typing import List, Tuple

# Type alias for step handlers
StepHandler = Callable[[str, Any, PostgresStorage], Awaitable[None]]


async def run_generation_flow(thread_id: str, storage: PostgresStorage) -> None:
    workflow = await storage.get_workflow(thread_id)
    if not workflow:
        logfire.error(
            "Workflow not found for thread {thread_id}, creating workflow",
            thread_id=thread_id,
        )
        raise HTTPException(status_code=404, detail="Workflow not found")

    print(f"Running generation flow for thread {thread_id}")

    # Define ordered flow steps as tuples (from_status, to_status, handler)
    flow_steps: List[Tuple[WorkflowStatus, WorkflowStatus, StepHandler]] = [
        (WorkflowStatus.STARTED, WorkflowStatus.BRIEFING_COMPLETE, _run_briefing_step),
        (
            WorkflowStatus.BRIEFING_COMPLETE,
            WorkflowStatus.STRATEGY_COMPLETE,
            _run_strategy_step,
        ),
        (
            WorkflowStatus.STRATEGY_COMPLETE,
            WorkflowStatus.CALENDAR_COMPLETE,
            _run_calendar_step,
        ),
        (
            WorkflowStatus.CALENDAR_COMPLETE,
            WorkflowStatus.IMAGES_COMPLETE,
            _run_images_step,
        ),
        (WorkflowStatus.IMAGES_COMPLETE, WorkflowStatus.HTML_COMPLETE, _run_html_step),
    ]

    # Execute steps starting from current status
    for from_status, to_status, handler in flow_steps:
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if workflow.status == from_status:
            await handler(thread_id, workflow, storage)
            workflow = await storage.get_workflow(thread_id)  # Refresh workflow state


async def _run_briefing_step(
    thread_id: str, workflow: AutoMarketState, storage: PostgresStorage
) -> None:
    briefing = await briefing_agent.run(workflow.conversation_transcript)
    print(f"Briefing created for thread {thread_id}, briefing={briefing.output}")

    workflow.briefing_md = briefing.output
    workflow.status = WorkflowStatus.BRIEFING_COMPLETE
    await storage.update_workflow(workflow)


async def _run_strategy_step(
    thread_id: str, workflow: AutoMarketState, storage: PostgresStorage
) -> None:
    strategy = await strategy_agent.run(workflow.briefing_md)
    print(f"Strategy created for thread {thread_id}, strategy={strategy.output}")

    workflow.strategy_and_plan_md = strategy.output
    workflow.status = WorkflowStatus.STRATEGY_COMPLETE
    await storage.update_workflow(workflow)


async def _run_calendar_step(
    thread_id: str, workflow: AutoMarketState, storage: PostgresStorage
) -> None:
    calendar = await calendar_agent.run(workflow.strategy_and_plan_md)
    print(f"Calendar created for thread {thread_id}, calendar={calendar.output}")

    workflow.calendar_events = calendar.output
    workflow.status = WorkflowStatus.CALENDAR_COMPLETE
    await storage.update_workflow(workflow)


calendar_events_ta = TypeAdapter(list[CalendarPost])


async def _run_images_step(
    thread_id: str, workflow: AutoMarketState, storage: PostgresStorage
) -> None:
    posts_with_images: list[tuple[CalendarPost, list[str]]] = []

    if not workflow.calendar_events:
        raise HTTPException(status_code=404, detail="Calendar events not found")
    for post in calendar_events_ta.validate_json(str(workflow.calendar_events)):
        image_prompts = await image_prompt_agent.run(f"""
        date: {post.date}
        title: {post.title}
        description: {post.description}
        """)
        print(
            f"Image prompts created for thread {thread_id}, image_prompts={image_prompts.output}, post={post}"
        )
        posts_with_images.append((post, image_prompts.output))

    # Store posts_with_images if needed for later steps
    workflow.status = WorkflowStatus.IMAGES_COMPLETE
    await storage.update_workflow(workflow)


async def _run_html_step(
    thread_id: str, workflow: AutoMarketState, storage: PostgresStorage
) -> None:
    html = await html_agent.run(workflow.strategy_and_plan_md)
    print(f"HTML created for thread {thread_id}, html={html.output}")

    workflow.html_content = html.output
    workflow.status = WorkflowStatus.HTML_COMPLETE
    await storage.update_workflow(workflow)
