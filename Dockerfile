FROM python:3.13-alpine

ENV APP_HOME /app

WORKDIR $APP_HOME

COPY . $APP_HOME

RUN pip install -r requirements.txt

EXPOSE 3000

ENTRYPOINT ["python", "main.py"]
