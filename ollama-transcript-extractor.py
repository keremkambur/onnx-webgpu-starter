import asyncio
import os
import requests
import json
from typing import Optional
import re

# Import the new utility function
from utils import get_formatted_datetime

from langchain_ollama import ChatOllama
from browser_use import Agent, Browser, Controller
from pydantic import BaseModel

# --- Final, Correct Initializer using your most powerful local model ---
OLLAMA_API_BASE_URL = "https://ollama-client.makinarota.com"

ollamaLlm = ChatOllama(
    #model='qwen2.5:14b-instruct-q4_0', # Using your most powerful available model
    model='gemma3:12b', # Using your most powerful available model
    num_ctx=8192,
    base_url=OLLAMA_API_BASE_URL,
    temperature=0.0, # Setting temperature to 0 for maximum predictability
    format="json",
    # Increased timeout to 5 minutes to prevent connection errors on the large initial prompt
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
        # Calling Browser() directly
        async with Browser() as browser:
            # Programmatically navigate to the start URL
            print("▶️ Programmatically navigating to the starting URL...")
            await browser.navigate_to("https://www.youtube.com/watch?v=2E140N7NfG4")
            print("✅ Navigation complete. Starting agent.")

            # Get a unique timestamp for this run's output files
            run_timestamp = get_formatted_datetime()

            agent = Agent(
                task=(
                    """
                    **Your Core Directive: Chain of Thought**
                    You are a web automation agent. You must use a step-by-step thinking process to achieve your goal.
                    
                    1.  **OBSERVE:** Look at the current page and the interactive elements.
                    2.  **PLAN:** Compare the page to the overall plan and state the single next step.
                    3.  **ACTION:** Choose the one concrete tool action (like `click_element_by_index` or `extract_content`) that achieves that single next step. Do not use 'unknown()'.
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
                # Use the timestamp to create a unique GIF filename
                generate_gif=f"agent_history_{run_timestamp}.gif",
                use_vision=False, # This model is not a vision model
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
