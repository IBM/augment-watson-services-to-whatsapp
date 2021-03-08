FROM python:3.6-slim
LABEL maintainer="Manoj Jahgirdar <manoj.jahgirdar@in.ibm.com>"
WORKDIR /app

ADD . /app

# RUN apt-get update && apt-get install -y libpq-dev gcc
# # need gcc to compile psycopg2
# RUN pip3 install psycopg2~=2.6
# RUN apt-get autoremove -y gcc
RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 8080

CMD ["python", "-u", "app.py"]