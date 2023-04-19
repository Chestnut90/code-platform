FROM python:3.10.8

# ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

ENV PYTHONPATH=${PYTHONPATH}:${PWD}
COPY pyproject.toml /app/
COPY ./code-platform /app/

# install python packages
# RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -
RUN pip install "poetry==1.2.2"
RUN poetry config virtualenvs.create false
RUN poetry install --no-root