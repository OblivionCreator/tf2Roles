docker prune
docker build -t rwu-roles .
docker save rwu-roles -o ~/docker-store/rwu-roles.tar