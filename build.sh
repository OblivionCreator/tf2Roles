docker prune
docker build -t rdl-roles .
docker save rdl-roles -o ~/docker-store/rdl-roles.tar