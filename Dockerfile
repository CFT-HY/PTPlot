FROM python:3.13

ENV PYTHONBUFFERED=1
RUN apt-get update \
    && apt-get install -y cmake gfortran \
    && apt-get clean
COPY manage.py requirements.txt /ptplot/
COPY ./ptplot /ptplot/ptplot/
COPY ./ptplot_site /ptplot/ptplot_site/
WORKDIR /ptplot
RUN chmod 0444 /ptplot/requirements.txt \
    && python -m pip install --upgrade pip --no-cache-dir \
    && pip install -r requirements.txt --no-cache-dir
# python manage.py collectstatic

ENTRYPOINT ["gunicorn", "ptplot.wsgi", "--bind", "0.0.0.0:8000"]
