FROM python:3.10-bullseye

RUN apt-get update && apt-get upgrade -y
RUN apt-get install tesseract-ocr tesseract-ocr-deu poppler-utils -y

COPY . /firefax/
WORKDIR /firefax/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python3", "/firefax/src/telegram_bot.py"]
