FROM alpine
RUN apk add --no-cache nginx \
 && echo "user root;" > /etc/nginx/nginx.conf \
 && echo "daemon off;" >> /etc/nginx/nginx.conf \
 && echo "worker_processes 1;" >> /etc/nginx/nginx.conf \
 && echo "pid /var/run/nginx.pid;" >> /etc/nginx/nginx.conf \
 && echo "error_log /dev/stderr info;" >> /etc/nginx/nginx.conf \
 && echo "events {" >> /etc/nginx/nginx.conf \
 && echo "    worker_connections  1024;" >> /etc/nginx/nginx.conf \
 && echo "}" >> /etc/nginx/nginx.conf \
 && echo "" >> /etc/nginx/nginx.conf \
 && echo "http {" >> /etc/nginx/nginx.conf \
 && echo "    include /etc/nginx/mime.types;" >> /etc/nginx/nginx.conf \
 && echo "    default_type application/octet-stream;" >> /etc/nginx/nginx.conf \
 && echo "    log_format main '\$remote_addr - \$remote_user [\$time_local] \"\$request\" '" >> /etc/nginx/nginx.conf \
 && echo "                    '\$status $body_bytes_sent \"\$http_referer\" '" >> /etc/nginx/nginx.conf \
 && echo "                    '\"\$http_user_agent\" \"\$http_x_forwarded_for\"';" >> /etc/nginx/nginx.conf \
 && echo "    access_log /dev/stdout main;" >> /etc/nginx/nginx.conf \
 && echo "    sendfile on;" >> /etc/nginx/nginx.conf \
 && echo "    tcp_nopush on;" >> /etc/nginx/nginx.conf \
 && echo "    tcp_nodelay on;" >> /etc/nginx/nginx.conf \
 && echo "    keepalive_timeout 65;" >> /etc/nginx/nginx.conf \
 && echo "    server {" >> /etc/nginx/nginx.conf \
 && echo "        listen 8081;" >> /etc/nginx/nginx.conf \
 && echo "        server_name localhost;" >> /etc/nginx/nginx.conf \
 && echo "        location / {" >> /etc/nginx/nginx.conf \
 && echo "            root /data;" >> /etc/nginx/nginx.conf \
 && echo "            autoindex on;" >> /etc/nginx/nginx.conf \
 && echo "        }" >> /etc/nginx/nginx.conf \
 && echo "        location = /sitemap.txt {" >> /etc/nginx/nginx.conf \
 && echo "            root /;" >> /etc/nginx/nginx.conf \
 && echo "        }" >> /etc/nginx/nginx.conf \
 && echo "    }" >> /etc/nginx/nginx.conf \
 && echo "}" >> /etc/nginx/nginx.conf \
 && echo "" >> /etc/nginx/nginx.conf \
 && echo "#!/usr/bin/env sh" > /docker-entrypoint.sh \
 && echo "set -e" >> /docker-entrypoint.sh \
 && echo "" >> /docker-entrypoint.sh \
 && echo "find /data -type f | sed 's|^/data||' > /sitemap.txt" >> /docker-entrypoint.sh \
 && echo "" >> /docker-entrypoint.sh \
 && echo "exec \"\$@\"" >> /docker-entrypoint.sh \
 && chmod +x /docker-entrypoint.sh

EXPOSE 8081
VOLUME [ "/data" ]
ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD [ "nginx" ]
