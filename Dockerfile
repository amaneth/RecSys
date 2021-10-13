FROM python:3.8-slim
RUN mkdir /recommender
WORKDIR /recommender

COPY . /recommender

RUN apt-get update
RUN apt-get -y install gcc
RUN pip install --upgrade pip
RUN pip install -r /recommender/requirements.txt

