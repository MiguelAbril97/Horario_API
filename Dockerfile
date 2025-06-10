FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y gcc libpq-dev

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY . /app/

EXPOSE 8000

#En producción:
#CMD ["gunicorn", "horario.wsgi:application", "--bind", "0.0.0.0:8000"]

# desarrollo:
 CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
