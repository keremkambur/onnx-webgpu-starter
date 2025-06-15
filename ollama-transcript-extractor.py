import asyncio
import os
import requests
import json
from typing import Optional
import re

# Import the utility function for timestamped filenames
from utils import get_formatted_datetime

from langchain_ollama import ChatOllama
# Import BrowserConfig which is required for headless/containerized environments
from browser_use import Agent, Browser, BrowserConfig, Controller
from pydantic import BaseModel

# --- Set the base URL for the local Ollama server ---
# Using host.docker.internal is correct for connecting from a dev container to the host machine
OLLAMA_API_BASE_URL = "http://host.docker.internal:11434"

# --- LLM Initializer ---
ollamaLlm = ChatOllama(
    model='gemma3:12b', # Using the model from your last test run
    num_ctx=8192,
    base_url=OLLAMA_API_BASE_URL,
    temperature=0.0, # Setting temperature to 0 for maximum predictability
    format="json",
    # A generous timeout for the large initial prompt
    client_kwargs={"timeout": 300.0}
)

desiredLlm = ollamaLlm

# --- Pydantic Models for Data Extraction ---
class Transcription(BaseModel):
    timestamp: str
    transcribed_text: str

class Transcriptions(BaseModel):
    transcriptions: list[Transcription]

controller = Controller(output_model=Transcriptions)

# --- Main Asynchronous Function ---
async def run_search():
    try:
        # Create a BrowserConfig/Profile to disable the sandbox for the container.
        browser_profile = BrowserConfig(chromium_sandbox=False)
        
        # Pass the profile to the Browser constructor to launch correctly.
        async with Browser(browser_profile=browser_profile) as browser:
            # Programmatically navigate to the start URL
            print("▶️ Programmatically navigating to the starting URL...")
            await browser.navigate_to("https://www.youtube.com/watch?v=2E140N7NfG4")
            print("✅ Navigation complete. Starting agent.")

            run_timestamp = get_formatted_datetime()

            agent = Agent(
                task=(
                    """
                    **Your Core Directive: Chain of Thought**
                    You are a web automation agent. Follow these steps on every turn:
                    1.  **OBSERVE:** Look at the current page.
                    2.  **PLAN:** State the single next step from the OVERALL PLAN below.
                    3.  **ACTION:** Choose the one concrete tool to achieve that step. A click action MUST look like this: `[{"click_element_by_index": {"index": 123}}]`. You are FORBIDDEN from using 'unknown()'.
                    4.  **RESPOND:** Format your thinking and action into the required JSON.

                    **JSON FORMAT RULE:**
                    Your response MUST be a valid JSON object with "current_state" and "action" keys.

                    ---
                    **OVERALL PLAN:**
                    1. Click the "Accept All" button if it exists.
                    2. Click the "Show more" button in the description.
                    3. Click the "Show transcript" button.
                    4. Use `extract_content` to get the transcript text and timestamps.
                    5. Use `finish` to return the scraped data in a JSON structure like: {"transcriptions": [{"timestamp": "...", "transcribed_text": "..."}]}.
                    """
                ),
                llm=desiredLlm,
                controller=controller,
                browser=browser,
                max_actions_per_step=1,
                generate_gif=f"agent_history_{run_timestamp}.gif",
                use_vision=False,
            )

            print("🚀 Starting agent execution...")
            history = await agent.run()

            print("📄 Agent execution completed. Processing results...")
            result = history.final_result()
            
            if result:
                print("✅ Results found, processing...")
                try:
                    if isinstance(result, str):
                        json_match = re.search(r'\{.*\}', result, re.DOTALL)
                        json_str = json_match.group() if json_match else result
                        result_data = json.loads(json_str)
                    else:
                        result_data = result
                    
                    parsed: Transcriptions = Transcriptions.model_validate(result_data)
                    
                    # Use the timestamp to create a unique JSON filename
                    output_file = f'transcriptions_{run_timestamp}.json'
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(parsed.model_dump_json(indent=4))
                    
                    print(f"✅ Successfully wrote {len(parsed.transcriptions)} transcriptions to {output_file}")
                    
                except Exception as e:
                    print(f"❌ Error processing results: {e}")
                    print(f"Raw result: {result}")
            else:
                print('❌ No result returned from agent')
                
    except Exception as e:
        print(f"❌ Error during execution: {e}")

if __name__ == '__main__':
    print("🎬 YouTube Transcript Scraper Starting...")
    asyncio.run(run_search())
