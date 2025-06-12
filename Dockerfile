# Start from the official Python 3.11 dev container image
FROM mcr.microsoft.com/devcontainers/python:3.11

WORKDIR /workspaces/browser-use-test

# Copy only the requirements file to leverage Docker's layer caching
COPY requirements.txt .

# Install dependencies using a persistent cache mount for pip.
# This layer is rebuilt only when requirements.txt changes, AND
# when it does, pip will use the mounted cache to avoid re-downloading.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt \
    && playwright install-deps && playwright install --with-deps firefox

# Now, copy the rest of the application code.
COPY . .