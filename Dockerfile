FROM python:3.8

LABEL description="ReservationAPI-image for the class 'Enterprise Information Management' in summer 2023."

WORKDIR /code

COPY ./requirements.txt code/requirements.txt

RUN pip install --no-cache-dir --upgrade --no-dependencies -r code/requirements.txt

COPY ./src /code/src

COPY ./conf /code/conf

ARG PORT=80

EXPOSE $PORT

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "$PORT"]