
FROM python:3.6

WORKDIR /project_hollywood

COPY . .

RUN apt-get update
RUN apt-get -y install sudo
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

#Install components needed for Semantic UI
#RUN curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
#RUN sudo apt-get install -y nodejs
#RUN npm install -g gulp
#RUN cd flaskr && \
#    npm install fomantic-ui && \
#    cd semantic && \
#    npx gulp build



RUN pip install -r requirements.txt

ENV FLASK_APP=flaskr
ENV FLASK_ENV=development


#ENTRYPOINT uwsgi --http :8080 --module 'flaskr.__init__:create_app()'
ENTRYPOINT gunicorn -w 2 -p :8080  "flaskr.__init__:create_app()" --timeout 25200





