FROM python:3.10-bullseye

RUN apt-get update && apt-get upgrade -y
RUN apt-get install apt-transport-https lsb-release poppler-utils -y

RUN echo "deb https://notesalexp.org/tesseract-ocr-dev/$(lsb_release -cs)/ $(lsb_release -cs) main" \
| tee /etc/apt/sources.list.d/notesalexp.list > /dev/null
RUN apt-get update -oAcquire::AllowInsecureRepositories=true
RUN apt-get install notesalexp-keyring -oAcquire::AllowInsecureRepositories=true --allow-unauthenticated -y

RUN apt-get update && apt-get upgrade -y
RUN apt-get install tesseract-ocr tesseract-ocr-deu -y

COPY . /firefax/
WORKDIR /firefax/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python3", "/firefax/src/telegram_bot.py"]
