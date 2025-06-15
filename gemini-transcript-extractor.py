import asyncio
import os
import requests
import json
from typing import Optional
import re

from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, Controller
from pydantic import BaseModel
from utils import get_formatted_datetime

# Using a powerful instruction-tuned model
geminiLlm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    temperature=0.0
)

desiredLlm = geminiLlm

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
        async with Browser() as browser:
            # Programmatically navigate to the start URL
            print("▶️ Programmatically navigating to the starting URL...")
            # CORRECTED: Using the proper 'navigate_to' method
            await browser.navigate_to("https://www.youtube.com/watch?v=2E140N7NfG4")
            print("✅ Navigation complete. Starting agent.")

            agent = Agent(
                task=(
                    """
                    **JSON RULE:** Your response must be a valid JSON object with "current_state" and "action" keys. You must choose a specific action; do not use 'unknown()'.

                    **EXECUTE THIS PLAN:**
                    1. Click the "Accept All" button if it exists.
                    2. Click the "Show more" button in the description.
                    3. Click the "Show transcript" button.
                    4. Use `extract_content` to get the transcript text and timestamps.
                    5. Use `finish` with the scraped data, like this: {"transcriptions": [{"timestamp": "...", "transcribed_text": "..."}]}.
                    """
                ),
                llm=desiredLlm,
                controller=controller,
                browser=browser,
                max_actions_per_step=1,
                generate_gif=".execution-artifacts/gemini-"+get_formatted_datetime()+".gif",
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
                    
                    output_file = ".execution-artifacts/gemini-transcriptions-"+get_formatted_datetime()+".json"
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
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY environment variable not set. Please set it before running.")
        exit(1)
    asyncio.run(run_search())
