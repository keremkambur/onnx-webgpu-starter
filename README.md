# Browser Use Test

## Project Description

This project demonstrates the use of the `browser-use` library for web automation and data extraction. It uses `langchain-ollama` and `langchain-google-genai` to interact with language models. It also uses `playwright` to control the browser.

## Installation

1.  Install Docker and VS Code Dev Containers extension.
2.  Clone the repository.
3.  Open the repository in VS Code.
4.  Reopen in Container.
5.  Install the dependencies:

    ```bash
    pip3 install -r requirements.txt
    ```

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
