FROM python:3.8-slim
RUN mkdir /recommender
WORKDIR /recommender


RUN apt-get update
RUN apt-get -y install gcc
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt --timeout 600
COPY . /recommender
