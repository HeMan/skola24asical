FROM python:3-alpine
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
EXPOSE 2424
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./skola24asical.py /code/skola24asical.py
CMD ["uvicorn", "skola24asical:app", "--host", "0.0.0.0", "--port", "2424"]

