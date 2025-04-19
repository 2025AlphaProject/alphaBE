FROM python:3.12

WORKDIR /code
COPY ./requirements.txt /code/
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y libgl1
COPY . /code/
EXPOSE 8000