FROM ruby

RUN gem install sass

WORKDIR /tmp
ENTRYPOINT ["sass", "--watch", "/src/sass:/src", "--sourcemap=none", "--style=compressed"]
