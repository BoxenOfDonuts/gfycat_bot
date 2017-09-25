FROM hypriot/rpi-alpine:latest

# install Dependencies
RUN apk update && apk add --no-cache python3

# add files
ADD . /gfycat
WORKDIR /gfycat

# install pip dependencies
RUN pip3 install -r requirements.txt

CMD python3 gfycat_bot.py
