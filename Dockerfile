FROM python:3.12

WORKDIR /code
RUN apt-get update && apt-get install -y libgl1
COPY ./requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
EXPOSE 8000