from pydantic import BaseModel
from langchain_ollama import ChatOllama
from browser_use import Agent
import asyncio
from playwright.async_api import async_playwright
from browser_use import BrowserConfig, Browser, Controller
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from typing import List

# Define the output format as a Pydantic model
class Car(BaseModel):
	menzil: str
 
controller = Controller(output_model=Car)
 
# Basic configuration
config = BrowserConfig(
    headless=True,
    disable_security=True,
    
)


# browser = Browser(config=config)

# contextConfig = BrowserContextConfig(minimum_wait_page_load_time=0.5)
# browserContext = BrowserContext(browser=browser, config=contextConfig)

# Initialize the model
# llm=ChatOllama(model="qwen3:14b", num_ctx=32000, 
#     base_url="http://host.docker.internal:11434")
async def main():
    # Ensure the LLM is initialized with the correct address for the host
    llm=ChatOllama(
        model="qwen2.5:latest",
        base_url="http://host.docker.internal:11434", # This line is critical
        num_ctx=32000
    )

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        browserContext = BrowserContext(browser=browser, config=BrowserContextConfig(minimum_wait_page_load_time=0.5))
        
        try:
            # Initialize the agent
            agent = Agent(
                task="Navigate https://www.tesla.com/tr_tr/modely/design close any banner/pop ups after page is fully loaded and return span value just next to the span with value 'km' ",
                browser=browser,
                browser_context=browserContext,
                llm=llm,
            )

            # --- This logic MUST be inside the try block ---
            history = await agent.run()
            print(history)
            result = history.final_result()
    
            if result:
                parsed: Car = Car.model_validate_json(result)
                print(parsed)

        except Exception as e:
            # This will now give a much more specific error message
            print(f"An error occurred: {e}")
        
        finally:
            # This ensures the browser always closes
            print("Closing browser...")
            await browser.close()
asyncio.run(main())