# Use official lightweight Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory in container
WORKDIR /app

# Enable bytecode compilation to speed up execution
ENV UV_COMPILE_BYTECODE=1

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Sync dependencies (cached layer)
RUN uv sync --frozen --no-install-project

# Copy project files
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Command to run the application (binding to 0.0.0.0 for external access)
CMD ["uv", "run", "streamlit", "run", "ui/app.py", "--server.address=0.0.0.0"]
