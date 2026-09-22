# Todo: Use the PTtools container as the base image once it has proper version tags
# When updating the Python version here,
# also update it in .python-version, the GitHub Actions workflows and .readthedocs.yaml
FROM python:3.14

# Install uv, which is used for installing the Python dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONBUFFERED=1
# Compile the Python files to bytecode to speed up the startup
ENV UV_COMPILE_BYTECODE=1
# Run in the virtualenv that uv creates
ENV PATH="/ptplot/.venv/bin:${PATH}"
EXPOSE 8000

# Install generic dependencies
RUN apt-get update \
    && apt-get install -y cmake gfortran \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install project dependencies
# The project itself is not installed, as its source is copied to the image below.
COPY LICENSE README.md pyproject.toml uv.lock /ptplot/
WORKDIR /ptplot
RUN uv sync --locked --no-cache --no-default-groups --no-install-project

# Copy the project
COPY manage.py /ptplot/
COPY ./ptplot /ptplot/ptplot/
COPY ./ptplot_site /ptplot/ptplot_site/
# RUN python manage.py collectstatic

ENTRYPOINT ["gunicorn", "ptplot_site.wsgi", "--bind", "0.0.0.0:8000"]
