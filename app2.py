import asyncio
import os
import requests
import json
from typing import Optional

# It's better to explicitly read the environment variable than to rely on dotenv here
#OLLAMA_API_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_BASE_URL = "https://ollama-client.makinarota.com"
from langchain_ollama import ChatOllama
from browser_use import Agent, BrowserConfig, Browser, Controller
from browser_use.agent.service import ToolCallingMethod
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI


# ==================== ADD THIS ENTIRE BLOCK ====================
def patch_browser_use_agent():
    """
    Patch browser-use Agent to completely bypass tool calling detection
    for the problematic qwen2.5-vl model by forcing 'raw' mode.
    """
    from browser_use.agent.service import Agent as BrowserUseAgent

    def patched_set_tool_calling_method(self):
        """
        This patched method skips detection and directly returns 'raw'.
        'raw' mode is the most basic text-in, text-out method and avoids
        the capability checks that are causing the qwen model to fail.
        """
        print("🔧 Bypassing LLM capability detection for qwen2.5-vl.")
        print("✅ Forcing 'raw' tool calling method.")
        return 'raw'

    # Apply the single, targeted patch to the function that performs detection.
    BrowserUseAgent._set_tool_calling_method = patched_set_tool_calling_method
    print("🔧 Browser-use Agent has been patched successfully.")

# Apply the patch immediately after defining it.
patch_browser_use_agent()
# ===============================================================


def test_ollama_connection(base_url):
    """Test if Ollama is accessible"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"✅ Ollama is accessible at {base_url}")
            models = response.json().get('models', [])
            print(f"Available models: {[model['name'] for model in models]}")
            return True
        else:
            print(f"❌ Ollama responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Ollama at {base_url}: {e}")
        return False

# Test connection before proceeding
print(f"Testing Ollama connection at {OLLAMA_API_BASE_URL}...")
if not test_ollama_connection(OLLAMA_API_BASE_URL):
    print("Trying alternative URLs...")
    alternative_urls = [
        "http://127.0.0.1:11434",
        "http://host.docker.internal:11434",
        "http://localhost:11434"
    ]
    
    connection_found = False
    for url in alternative_urls:
        if test_ollama_connection(url):
            OLLAMA_API_BASE_URL = url
            connection_found = True
            break
    
    if not connection_found:
        print("❌ Could not connect to Ollama. Please ensure:")
        print("1. Ollama is running: ollama serve")
        print("2. Required models are installed: ollama pull qwen2.5-vl:7b && ollama pull nomic-embed-text")
        exit(1)

geminiLlm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

ollamaLlm = ChatOllama(
    # Use the original model name, since the server now handles GPU layers correctly
    model='qwen2.5vl:7b',
    
    # Set context size to the effective limit to prevent thrashing and high CPU/GPU usage
    num_ctx=8192,
    
    # Your other parameters remain
    base_url=OLLAMA_API_BASE_URL,
    temperature=0.1,
    top_p=0.9,
    
    # Ensure parsable output for your data extraction task
    format="json",
    
    # The correct way to set a request timeout as a safeguard
    client_kwargs={"timeout": 120.0}
)
# You can switch between LLMs here
# Stick with qwen2.5-vl:7b as requested
desiredLlm = ollamaLlm

class Transcription(BaseModel):
    timestamp: str
    transcribed_text: str

class Transcriptions(BaseModel):
    transcriptions: list[Transcription]

controller = Controller(output_model=Transcriptions)

async def run_search():
    try:
        # Define a browser configuration to disable the sandbox
        browser_config = BrowserConfig(
            chromium_sandbox=False,
            # Add headless=False if you want to see the browser in action
            # headless=False,
        )

        # Create a Browser instance with our custom configuration
        async with Browser(config=browser_config) as browser:
            # Define the memory configuration explicitly using the variable
            memory_config = {
                "memory": {
                    "embedding_model": {
                        "provider": "ollama",
                        "config": {
                            "model": "nomic-embed-text",
                            "base_url": OLLAMA_API_BASE_URL
                        }
                    }
                }
            }

            # Create agent by passing the tool calling method directly
            # This is the correct, non-patching way.
            agent = Agent(
                task=(
                     """
        Your mission is to extract YouTube video transcriptions. Follow these steps precisely:
        1. Go to https://www.youtube.com/watch?v=2E140N7NfG4 and wait for the page to fully load.
        2. If a consent dialog appears, click the "Accept All" button.
        3. Click the "Show more" button in the video description to expand it.
        4. Find and click the "Show transcript" button.
        5. Wait for the transcript panel to appear and load completely.
            5.1. If there is no result found appears on transcript panel, close it by clicking X and click Show Transcript button again
            5.2 Continue with step 6
        6. Scrape all transcript segments. For each segment, extract the timestamp and the text.

        CRITICAL: Your final output MUST be a single JSON object and nothing else.
        The JSON object must conform to the structure: {"transcriptions": [{"timestamp": "...", "transcribed_text": "..."}]}.
        Do NOT include any other text, explanations, apologies, or markdown formatting like ```json.
        Your entire response must be only the valid JSON.
        """
                ),
                llm=desiredLlm,
                controller=controller,
                browser=browser,
                # ==============================
                max_actions_per_step=3,
                memory_config=memory_config,
                generate_gif=True,
                use_vision=True,
            )

            print("🚀 Starting agent execution...")
            history = await agent.run()

            
            print("📄 Agent execution completed. Processing results...")
            result = history.final_result()
            
            if result:
                print("✅ Results found, processing...")
                try:
                    # Try to parse as JSON first
                    if isinstance(result, str):
                        # Try to extract JSON from the result if it's embedded in text
                        import re
                        json_match = re.search(r'\{.*\}', result, re.DOTALL)
                        if json_match:
                            json_str = json_match.group()
                            result_data = json.loads(json_str)
                        else:
                            # If no JSON found, try to parse the whole thing
                            result_data = json.loads(result)
                    else:
                        result_data = result
                    
                    # Validate with controller if available
                    parsed: Transcriptions = Transcriptions.model_validate(result_data)
                    transcriptions_list = parsed.transcriptions
                    
                    # Save to file
                    output_file = 'transcriptions.json'
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(parsed.model_dump_json(indent=4))
                    
                    print(f"✅ Successfully wrote {len(transcriptions_list)} transcriptions to {output_file}")
                    
                    # Display first few transcriptions
                    print(f"\n📝 First few transcriptions:")
                    for i, transcription in enumerate(transcriptions_list[:5]):
                        print(f'{i+1:2d}. [{transcription.timestamp}] {transcription.transcribed_text}')
                    
                    if len(transcriptions_list) > 5:
                        print(f"... and {len(transcriptions_list) - 5} more transcriptions")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON result: {e}")
                    print(f"Raw result: {result}")
                    # Save raw result anyway
                    with open('raw_result.txt', 'w', encoding='utf-8') as f:
                        f.write(str(result))
                    print("Saved raw result to raw_result.txt")
                except Exception as e:
                    print(f"❌ Error processing results: {e}")
                    print(f"Raw result: {result}")
            else:
                print('❌ No result returned from agent')
                
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        raise

if __name__ == '__main__':
    print("🎬 YouTube Transcript Scraper Starting...")
    print("Make sure you have the required models:")
    print("  ollama pull qwen2.5-vl:7b")
    print("  ollama pull nomic-embed-text")
    print()
    
    asyncio.run(run_search())