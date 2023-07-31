FROM python:3.11

ENV DASH_DEBUG_MODE True

WORKDIR /app

COPY requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY src /app/src

EXPOSE 8050

CMD ["python", "./src/app.py"]