import httpx
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# --- Pydantic Models ---


class Attachment(BaseModel):
    url: str


class ModelConfiguration(BaseModel):
    model_id: Literal["v0-1.5-sm", "v0-1.5-md", "v0-1.5-lg", "v0-gpt-5"] = Field(
        ..., alias="modelId"
    )
    image_generations: Optional[bool] = Field(None, alias="imageGenerations")
    thinking: Optional[bool] = None


class EnvironmentVariable(BaseModel):
    key: str
    value: str


class File(BaseModel):
    object: str
    name: str
    content: str
    locked: bool
    url: Optional[str]


class Version(BaseModel):
    id: str
    object: str
    status: Literal["pending", "completed", "failed"]
    # demo_url: Optional[str] = Field(None, alias="demoUrl")
    created_at: str = Field(..., alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    # files: List[File]
    class Config:
        extra = "ignore"


class MessageFile(BaseModel):
    lang: str
    meta: dict
    source: str


class Message(BaseModel):
    id: str
    object: str
    content: str
    created_at: str = Field(..., alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    type: str
    role: Literal["user", "assistant"]
    finish_reason: Optional[str] = Field(None, alias="finishReason")
    api_url: str = Field(..., alias="apiUrl")
    files: Optional[List[MessageFile]] = None


class Chat(BaseModel):
    id: str
    object: str
    shareable: bool
    privacy: Literal["public", "private", "team", "team-edit", "unlisted"]
    name: Optional[str] = None
    title: Optional[str] = None
    created_at: str = Field(..., alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    favorite: bool
    demo: str
    # demoUrl: str
    author_id: str = Field(..., alias="authorId")
    project_id: Optional[str] = Field(None, alias="projectId")
    web_url: str = Field(..., alias="webUrl")
    api_url: str = Field(..., alias="apiUrl")
    latest_version: Optional[Version] = Field(None, alias="latestVersion")
    messages: List[Message]
    model_configuration: Optional[ModelConfiguration] = Field(
        None, alias="modelConfiguration"
    )


class Project(BaseModel):
    id: str
    object: str
    name: str
    privacy: Literal["private", "team"]
    vercel_project_id: Optional[str] = Field(None, alias="vercelProjectId")
    created_at: str = Field(..., alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    api_url: str = Field(..., alias="apiUrl")
    web_url: str = Field(..., alias="webUrl")
    description: Optional[str] = None
    instructions: Optional[str] = None
    chats: List[Chat]


# --- Request Models ---


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    environment_variables: Optional[List[EnvironmentVariable]] = Field(
        None, alias="environmentVariables"
    )
    instructions: Optional[str] = None


class CreateChatRequest(BaseModel):
    message: str
    system: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    chat_privacy: Optional[
        Literal["public", "private", "team-edit", "team", "unlisted"]
    ] = Field(None, alias="chatPrivacy")
    project_id: Optional[str] = Field(None, alias="projectId")
    model_configuration: ModelConfiguration = Field(..., alias="modelConfiguration")
    response_mode: Optional[Literal["sync", "async"]] = Field(
        None, alias="responseMode"
    )


class SendMessageRequest(BaseModel):
    message: str
    attachments: Optional[List[Attachment]] = None
    model_configuration: Optional[ModelConfiguration] = Field(
        None, alias="modelConfiguration"
    )
    response_mode: Optional[Literal["sync", "async"]] = Field(
        None, alias="responseMode"
    )


# --- API Client ---


class V0ApiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.v0.dev/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            headers=self.headers, base_url=self.base_url, timeout=httpx.Timeout(300000.0)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _post_and_handle(self, path: str, body: dict):
        print("sending request to v0", path, body)
        resp = await self.client.post(path, json=body)
        print("response from v0", resp.json())
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Try to parse JSON error details from the server (most helpful)
            try:
                details = resp.json()
            except Exception:
                details = resp.text
            # raise a more informative exception (or log) so you can debug
            raise RuntimeError(
                f"Request POST {path} failed with {resp.status_code}: {details}"
            ) from e
        return resp.json()

    async def create_project(self, project_data: CreateProjectRequest) -> Project:
        """
        Creates a new v0 project.
        """
        body = project_data.model_dump(by_alias=True, exclude_none=True)
        data = await self._post_and_handle("/projects", body)
        return Project(**data)

    async def create_chat(self, chat_data: CreateChatRequest) -> Chat:
        """
        Creates a new chat.
        """
        body = chat_data.model_dump(by_alias=True, exclude_none=True)
        data = await self._post_and_handle("/chats", body)
        return Chat(**data)

    async def send_message(
        self, chat_id: str, message_data: SendMessageRequest
    ) -> Chat:
        """
        Sends a message to an existing chat.
        """
        body = message_data.model_dump(by_alias=True, exclude_none=True)
        data = await self._post_and_handle(f"/chats/{chat_id}/messages", body)
        return Chat(**data)


# --- Example Usage (requires a valid API key and async context) ---


async def main():
    # Replace with your actual API key
    api_key = "YOUR_API_KEY"

    async with V0ApiClient(api_key=api_key) as client:
        # Example: Create a project
        try:
            project_data = CreateProjectRequest(
                name="My Awesome Project", description="This is a test project."
            )
            project = await client.create_project(project_data)
            print("--- Created Project ---")
            print(project.model_dump_json(indent=2))

            # Example: Get a project by ID
            retrieved_project = await client.get_project_by_id(project.id)
            print("\n--- Retrieved Project ---")
            print(retrieved_project.model_dump_json(indent=2))

            # Example: Create a chat
            chat_data = CreateChatRequest(
                message="Hello, world!",
                project_id=project.id,
                model_configuration=ModelConfiguration(modelId="v0-1.5-sm"),
            )
            chat = await client.create_chat(chat_data)
            print("\n--- Created Chat ---")
            print(chat.model_dump_json(indent=2))

            # Example: Send a message
            message_data = SendMessageRequest(message="This is a follow-up message.")
            updated_chat = await client.send_message(chat.id, message_data)
            print("\n--- Sent Message ---")
            print(updated_chat.model_dump_json(indent=2))

        except httpx.HTTPStatusError as e:
            print(f"An error occurred: {e}")
            print(e.response.text)


if __name__ == "__main__":

    # To run this example, you would need to uncomment the following line
    # and provide a valid API key.
    # asyncio.run(main())
    print("Client created successfully. See the example usage in the `main` function.")
