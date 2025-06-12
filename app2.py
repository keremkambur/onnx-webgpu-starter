import asyncio
import os

# It's better to explicitly read the environment variable than to rely on dotenv here
OLLAMA_API_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

from langchain_ollama import ChatOllama
from browser_use import Agent, BrowserConfig, Browser, Controller  # Import Browser
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI

geminiLlm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

ollamaLlm = ChatOllama(
    model='gemma3:12b',
    num_ctx=128000,
    base_url=OLLAMA_API_BASE_URL,
)

desiredLlm = ollamaLlm

class Transcription(BaseModel):
	timestamp: str
	transcribed_text: str


class Transcriptions(BaseModel):
	transcriptions: list[Transcription]


controller = Controller(output_model=Transcriptions)

async def run_search():
    # --- FIX: Define a browser configuration to disable the sandbox ---
    browser_config = BrowserConfig(
        chromium_sandbox=False,
        # You can add other browser settings here if needed
    )

    # --- FIX: Create a Browser instance with our custom configuration ---
    # We use 'async with' to ensure the browser is closed properly
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
        #6. grab the entire inner HTML of element starting with tag <ytd-transcript-renderer class="style-scope ytd-engagement-panel-section-list-renderer" panel-content-visible="" panel-target-id="engagement-panel-searchable-transcript"> as raw string
        

        agent = Agent(
            task=(
                """
                1. Go to https://www.youtube.com/watch?v=2E140N7NfG4 and wait until dialog /html/body/ytd-app/ytd-consent-bump-v2-lightbox appears
                2. Click Accept All  on appeared dialog window
                3. and then click the element with XPath: /html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-watch-metadata/div/div[4]/div[1]
                4. check inner elements of expanded element with XPath /html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-watch-metadata/div/div[4]/div[1] and locate Show Transcript button and click it
                5. this will open another panel with XPath /html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[2]/div/div[1]/ytd-engagement-panel-section-list-renderer[6]/div[2]/ytd-transcript-renderer/div[2]
                6. you will see elements with CSS classes 'segment-timestamp style-scope ytd-transcript-segment-renderer', in the inner HTML of each item is timestamp of the transcribed sentence
                7. you will also see elements with CSS classes 'segment-text style-scope ytd-transcript-segment-renderer', in the inner HTML of each item is transcribed sentence starting from the timestamp
                8. collect each pair of timestamp and transcribed texts (under each parent element with tag starting with <ytd-transcript-segment-renderer class="style-scope ytd-transcript-segment-list-renderer" rounded-container>)                 
                """
            ),
            llm=ollamaLlm,
            controller=controller,
            # --- FIX: Pass the pre-configured browser instance to the agent ---
            browser=browser,
            max_actions_per_step=1,
            memory_config=memory_config,
            generate_gif=True
        )
        history = await agent.run()
        print(history.final_result())
        result = history.final_result()
        if result:
            parsed: Transcriptions = Transcriptions.model_validate_json(result)
            with open('transcriptions.json', 'w', encoding='utf-8') as f:
                f.write(parsed.model_dump_json(indent=4))
            print("Successfully wrote formatted JSON to transcriptions.json")
            agent.stop()
            for transcription in parsed.transcriptions:
                print('\n--------------------------------')
                print(f'Title:            {transcription.timestamp}')
                print(f'URL:              {transcription.transcribed_text}')
        else:
            print('No result')


if __name__ == '__main__':
    # Make sure the embedding model is present on the host by running this
    # command in your HOST terminal (not in the container):
    # ollama pull nomic-embed-text
    
    print("Starting agent...")
    asyncio.run(run_search())
    
    
    # check each elements /html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[2]/div/div[1]/ytd-engagement-panel-section-list-renderer[6]/div[2]/ytd-transcript-renderer/div[2]/ytd-transcript-search-panel-renderer/div[2]/ytd-transcript-segment-list-renderer/div[1]/ytd-transcript-segment-renderer[1] like this and
    #             extract #segments-container > ytd-transcript-segment-renderer:nth-child(1) > div > div > div and #segments-container > ytd-transcript-segment-renderer:nth-child(1) > div > yt-formatted-string inner HTMLs 