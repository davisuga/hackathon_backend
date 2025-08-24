import asyncio
from typing import Any, Awaitable, Callable

from agno.tools.whatsapp import WhatsAppTools
from agno.utils.whatsapp import (
    send_image_message_async,
    upload_media_async,
)
import logfire
from fastapi import HTTPException
from pydantic import TypeAdapter

from .img_gen import generate_image

from .v0_client import (
    Attachment,
    ModelConfiguration,
    CreateChatRequest,
    V0ApiClient,
)

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
import os

# Type alias for step handlers
StepHandler = Callable[[str, Any, PostgresStorage], Awaitable[None]]
client = V0ApiClient(api_key=os.getenv("V0_API_KEY") or "")

wpp = WhatsAppTools()


async def _run_v0_page_step(
    thread_id: str, workflow: AutoMarketState, storage: PostgresStorage
) -> None:
    """
    Final step: push strategy/plan into v0.dev to create a hosted landing page.
    """
    user_number = await storage.get_number_by_thread_id(thread_id)
    brand_info = await storage.get_user_brand_by_thread_id(user_number)

    message = f"""
        You are an expert conversion copywriter and landing page strategist. Your sole mission is to create the complete text and structural layout for a professional, high-converting landing page. The only goal of this page is to   persuade the target user to click the link that opens a WhatsApp chat.
        user brand info: {brand_info}
        user phone number: {user_number}
        Analyze the provided briefing in detail:
        ---
        {workflow.briefing_md}
        ---
        And the strategy:
        ---
        {workflow.strategy_and_plan_md}
        ---
        Create a landing page and leave no empty image placeholders.
        """
    logo_url = brand_info.logo_url if brand_info else None

    async with client:
        chat = await client.create_chat(
            CreateChatRequest(
                projectId=None,
                message=message,
                chatPrivacy="public",
                modelConfiguration=ModelConfiguration(
                    modelId="v0-1.5-md",
                    imageGenerations=True,
                    thinking=True,
                ),
                responseMode="sync",
                attachments=[Attachment(url=logo_url)] if logo_url else None,
            )
        )

        workflow.page_url = chat.demo

        workflow.status = WorkflowStatus.HTML_COMPLETE
        await storage.update_workflow(workflow)
        await wpp.send_text_message_async(
            recipient=user_number,
            text="¡Listo! Tu landing page está lista. Puedes verla en el siguiente enlace: "
            + chat.demo,
        )


async def run_generation_flow(thread_id: str, storage: PostgresStorage) -> None:
    workflow = await storage.get_workflow(thread_id)
    if not workflow:
        logfire.error(
            "Workflow not found for thread {thread_id}, creating workflow",
            thread_id=thread_id,
        )
        conversation = await storage.get_conversation(thread_id=thread_id)
        workflow = await storage.create_workflow(thread_id=thread_id, transcript=conversation)
        # raise HTTPException(status_code=404, detail="Workflow not found")

    print(f"Running generation flow for thread {thread_id}")
    user_number = await storage.get_number_by_thread_id(thread_id)

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
            _make_run_images_step(number=user_number),
        ),
        # (
        #     WorkflowStatus.IMAGES_COMPLETE,
        #     WorkflowStatus.HTML_COMPLETE,
        #     _run_v0_page_step,
        # ),
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


def _make_run_images_step(number: str):
    async def _run_images_step(
        thread_id: str, workflow: AutoMarketState, storage: PostgresStorage
    ) -> None:
        if not workflow.calendar_events:
            raise HTTPException(status_code=404, detail="Calendar events not found")

        calendar_posts = calendar_events_ta.validate_json(str(workflow.calendar_events))
        master_prompt = await image_prompt_agent.run(workflow.briefing_md)

        async def process_single_post(post: CalendarPost) -> CalendarPost:
            """Process a single post to generate image prompts."""
            try:
                image = await generate_image(
                    f"""
                    {master_prompt}
                    title: {post.title}
                    description: {post.description}""",
                    resolution=post.resolution,
                )
                print(
                    f"Image prompts created for thread {thread_id}, image={image}, post={post}"
                )
                if not image:
                    raise HTTPException(
                        status_code=500, detail="Failed to generate image prompts"
                    )
                
                # Check if image is a dict or bytes
                if isinstance(image, dict):
                    post.image_url = image["image_url"]
                    image_bytes = image["image_bytes"]
                else:
                    # If it's bytes, we have an error in generate_image
                    raise HTTPException(
                        status_code=500, detail="Image generation returned invalid format"
                    )
                    
                media_id = await upload_media_async(
                    image_bytes,
                    mime_type="image/jpeg",
                    filename=f"{post.title.replace(' ', '_')}.jpg"
                )
                print(media_id)
                await send_image_message_async(
                    media_id=media_id,
                    recipient=number,
                )
                print("Image sent successfully")
            except Exception as e:
                print(f"Error processing post {post}: {e}")
                # Continue with the next post even if one fails
                pass
            return post

        # Run all image prompt generations concurrently
        posts_with_images = await asyncio.gather(
            *[process_single_post(post) for post in calendar_posts],
            return_exceptions=True,
        )

        # Handle any exceptions that occurred during processing
        successful_posts = []
        for i, result in enumerate(posts_with_images):
            if isinstance(result, Exception):
                print(f"Error processing post {calendar_posts[i]}: {result}")
                # You might want to handle this differently based on your requirements
                # For now, we'll skip failed posts
                continue
            successful_posts.append(result)

        posts_with_images = successful_posts
        workflow.calendar_events = posts_with_images
        # Store posts_with_images if needed for later steps
        workflow.status = WorkflowStatus.IMAGES_COMPLETE
        await storage.update_workflow(workflow)

    return _run_images_step


async def _run_html_step(
    thread_id: str, workflow: AutoMarketState, storage: PostgresStorage
) -> None:
    html = await html_agent.run(workflow.strategy_and_plan_md)
    print(f"HTML created for thread {thread_id}, html={html.output}")

    workflow.html_content = html.output
    workflow.status = WorkflowStatus.HTML_COMPLETE
    await storage.update_workflow(workflow)
