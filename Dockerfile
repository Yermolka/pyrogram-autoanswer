FROM python:3.10-slim

WORKDIR /usr/src/autoanswer

COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py"]