#!/bin/bash
docker build --force-rm -t viame/detector -f Dockerfile-viame-detector .
docker build --force-rm -t viame/scorer -f Dockerfile-viame-scorer .
docker build --force-rm -t socom/catalgo -f Dockerfile-cat-algorithm .
