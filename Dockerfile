FROM alpine:latest

# install Dependencies
RUN apk update && apk add --no-cache python3

# add files
ADD . /gfycat
WORKDIR /gfycat

# install pip dependencies
RUN apk update && apk add --no-cache python3 libxml2-dev libxslt-dev python3-dev g++

CMD python3 gfycat_bot.py
