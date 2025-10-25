import json
from google.adk.agents import SequentialAgent, LlmAgent
from .tools import youtube_search
from .prompt import youtube_search_agent_prompt, multimodal_agent_prompt, rank_agent_prompt
from pydantic import BaseModel
from google.adk.agents.callback_context import CallbackContext
from dotenv import load_dotenv
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
import google.auth
import os
from pydantic import BaseModel, HttpUrl
from typing import Optional,Dict,Any


class RankedVideo(BaseModel):
    """Represents the video selected by the ranking agent."""
    title: str
    url: HttpUrl

def search_tool_output_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict) -> Optional[Dict]:
    tool_context.state['search_results'] = tool_response
    tool_context.state['user_query'] = args["query"]
    return None

def rank_output_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    if llm_response.content and llm_response.content.parts:
        callback_context.state["selected_video"] = json.loads(llm_response.content.parts[0].text)
    return None

def build_llm_parts(video):
    parts = []
    parts.append(types.Part(text=f'Video: {video["title"]}'))
    parts.append(types.Part(text=f'url: {video["url"]}'))
    parts.append(types.Part(file_data=types.FileData(file_uri=video["url"], mime_type="video/*")))
    return parts

def vision_callback_builds_video_parts(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    video = callback_context.state["selected_video"]
    
    if video['url'] is None or video['url'] == "":
         llm_request.contents = [types.Content(role="user", parts=types.Part(text=f"No relevant video found for the user query reply to the user properly\n"))]
         return None

    user_query = callback_context.state["user_query"]
    modified_parts = [
        types.Part(text=f"Analyze this Youtube video based on the user query: {user_query}\n")
    ] + build_llm_parts(video)
    llm_request.contents = [types.Content(role="user", parts=modified_parts)]
    return None

# Load environment variables from .env file
load_dotenv()

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


youtube_search_agent = LlmAgent(
    model = 'gemini-2.5-flash',
    name = 'youtube_search_agent',
    instruction=youtube_search_agent_prompt,
    description="You are an helpful video search assistant to help the user to find relevant YouTube videos based on the user's query",
    after_tool_callback=search_tool_output_callback,
    tools=[youtube_search]
)

rank_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='rank_agent',
    instruction=rank_agent_prompt,
    description="You are an agent that selects the single best video from a list based on a user's query.",
    after_model_callback=rank_output_callback,
    output_schema=RankedVideo,
)

multimodal_agent = LlmAgent(
     model = 'gemini-2.5-pro',
     name = 'multimodal_agent',
     description="You are an helpful video analysis assistant to help identify key moments in a video on YouTube based on visual content analysis",
     before_model_callback=vision_callback_builds_video_parts,
     instruction=multimodal_agent_prompt,
)

root_agent = SequentialAgent(
    name="video_highlights_agent",
    sub_agents= [youtube_search_agent, rank_agent, multimodal_agent],
    description="An agent that finds and analyzes YouTube videos to identify key moments based on user queries."
)