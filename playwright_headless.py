import asyncio
from playwright.async_api import async_playwright

async def test_navigation():
    """
    Simple Playwright script to test basic web navigation and querying.
    """
    async with async_playwright() as p:
        # Launch browser in headless mode
        #await p.firefox.launch(headless=True)
        browser = await p.firefox.launch(headless=True)
        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
        page = await browser.new_page(user_agent=ua)
        try:
            # Navigate to a sample website
            await page.goto('https://www.tesla.com/tr_tr/modely/design#overview')
            
            element = page.locator('[data-id="range"]')

            # Navigate to the first span inside the div using CSS selector
            span_element = element.locator('span:first-child')

            # Get the text content of the span
            span_text = await span_element.text_content()
            print("span text:"+span_text)

        
        except Exception as e:
            print(f"Error during navigation: {e}")
        
        finally:
            await browser.close()

# Run the async function
if __name__ == '__main__':
    asyncio.run(test_navigation())