from google.adk.agents import SequentialAgent, LlmAgent
from .tools import search_youtube,convert_mmss_to_seconds
from .prompt import youtube_search_agent_prompt, multimodal_agent_prompt, rank_agent_prompt
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import google.auth
import os
from pydantic import BaseModel, HttpUrl
from typing import List

class VideoItem(BaseModel):
    """Represents a single video entry."""
    title: str
    url: HttpUrl  # Validates that the string is a valid HTTP/S URL
    timecode: str
    explanation: str
    visual_confidence: int

class VideoData(BaseModel):
    """Represents the main JSON structure containing a list of videos."""
    videos: List[VideoItem]

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
    tools=[search_youtube]
)

multimodal_agent = LlmAgent(
     model = 'gemini-2.5-pro',
     name = 'multimodal_agent',
     description="You are an helpful video analysis assistant to help identify key moments in a video on YouTube based on visual content analysis",
     output_schema=VideoData,
     instruction=multimodal_agent_prompt,
)

rank_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='rank_agent',
    instruction=rank_agent_prompt,
    description="You are an agent that ranks analyzed YouTube videos to find the most relevant one based on ranking",
    tools=[convert_mmss_to_seconds]
)

root_agent = SequentialAgent(
    name="video_highlights_agent",
    sub_agents= [youtube_search_agent, multimodal_agent, rank_agent ],
    description="An agent that finds and analyzes YouTube videos to identify key moments based on user queries."
)
