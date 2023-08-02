FROM python:3.11

ENV DASH_DEBUG_MODE True
ENV PYTHONPATH /src
ENV PYTHONUNBUFFERED 1

ADD src /src

COPY requirements.txt .
RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY . ./

EXPOSE 8050

CMD ["gunicorn", "-b", "0.0.0.0:8050", "src.app:server"]