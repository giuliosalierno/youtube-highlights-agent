from google.adk.agents import SequentialAgent, LlmAgent
from .tools import search_youtube
from .prompt import youtube_search_agent_prompt, multimodal_agent_prompt, rank_agent_prompt
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import google.auth
import os
# Load environment variables from .env file
load_dotenv()

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


class LLMRankedOutput(BaseModel):
    explanation: str = Field(description="The reason why this video has been chosen as the most relevant one")
    title: str = Field(description="The title of the top Youtube Video")
    url: str = Field(description="The url of the top Youtube Video")
    timecode: str = Field(description="The timecode of the top Youtube Video in the format MM:SS")


youtube_search_agent = LlmAgent(
    model = 'gemini-2.5-flash',
    name = 'youtube_search_agent',
    instruction=youtube_search_agent_prompt,
    description="You are an helpful video search assistant to help the user to find key moments in a video on YouTube",
    tools=[search_youtube]
)

multimodal_agent = LlmAgent(
     model = 'gemini-2.5-pro',
     name = 'multimodal_agent',
     instruction=multimodal_agent_prompt,
)

rank_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='rank_agent',
    instruction=rank_agent_prompt,
    output_schema=LLMRankedOutput
)

root_agent = SequentialAgent(
    name="video_highlights_agent",
    sub_agents= [youtube_search_agent, multimodal_agent, rank_agent ],
    description="Executes a sequence of agents to answer the user's question"
)
