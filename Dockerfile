# Todo: Use the PTtools container as the base image once it has proper version tags
FROM python:3.14

ENV PYTHONBUFFERED=1
EXPOSE 8000

# Install generic dependencies
RUN apt-get update \
    && apt-get install -y cmake gfortran \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade --root-user-action=ignore --no-cache-dir pip wheel

# Install project dependencies
COPY manage.py requirements.txt /ptplot/
WORKDIR /ptplot
RUN chmod 0444 /ptplot/requirements.txt \
    && pip install --root-user-action=ignore --no-cache-dir -r requirements.txt

# Copy the project
COPY ./ptplot /ptplot/ptplot/
COPY ./ptplot_site /ptplot/ptplot_site/
# python manage.py collectstatic

ENTRYPOINT ["gunicorn", "ptplot_site.wsgi", "--bind", "0.0.0.0:8000"]
