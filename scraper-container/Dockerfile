FROM python:3.10

# Install manually all the missing libraries
RUN apt-get update 
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


# # Copy local code to the container image.
ENV APP_HOME=/app
WORKDIR $APP_HOME
COPY ./*py .
COPY ./lol_oracle_jsonkey.json .


# don't hardcode api key wtf
ENTRYPOINT [ "python3", "scraper.py", "RGAPI-44534f77-bda9-44e5-bb07-79f4cb1eb4e9" ]