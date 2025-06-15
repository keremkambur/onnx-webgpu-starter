# Browser Use Test

## Project Description

This project demonstrates the use of the `browser-use` library for web automation and data extraction. It uses `langchain-ollama` and `langchain-google-genai` to interact with language models. It also uses `playwright` to control the browser. `playwright_headless.py` provides a reference usage for Playwright.

## Installation

### Option 1: Using Docker

1.  Install Docker and VS Code Dev Containers extension.
2.  Clone the repository.
3.  Build the Docker image:

    ```bash
    docker build -t browser-use-test .
    ```

4.  Run the Docker container:

    ```bash
    docker run -it --rm -p 8888:8888 browser-use-test
    ```

### Option 2: Using VS Code Dev Containers for Debugging

1.  Install Docker and VS Code Dev Containers extension.
2.  Clone the repository.
3.  Open the repository in VS Code.
4.  Reopen in Container.
5.  Install the dependencies:

    ```bash
    pip3 install -r requirements.txt
    ```

6.  Set the environment variables in the `.devcontainer/devcontainer.json` file as described in the Configuration section.
7.  You can now debug the application by setting breakpoints and running the desired script (e.g., `app.py`) in the VS Code debugger.

## Configuration

The following environment variables need to be configured:

*   `OLLAMA_BASE_URL`: The base URL for the Ollama API. Default value is `http://host.docker.internal:11434`.
*   `GOOGLE_API_KEY`: The API key for the Google Generative AI API.

These variables can be set in the `.devcontainer/devcontainer.json` file:

```json
"containerEnv": {
    "OLLAMA_BASE_URL": "http://host.docker.internal:11434",
    "GOOGLE_API_KEY": "YOUR_GOOGLE_API_KEY"
}
```

## Usage

1.  Run `app.py` to navigate to the Tesla website and extract data:

    ```bash
    python3 app.py
    ```

2.  Run `app2.py` to extract transcriptions from a YouTube video:

    ```bash
    python3 app2.py
