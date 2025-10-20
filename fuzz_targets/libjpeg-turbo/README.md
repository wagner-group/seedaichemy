### 1. Corpus setup

Add the seed files to `/corpus`.

### 2. Image building

`docker build -t fuzz-libjpeg-turbo .`

### 3. Run the Docker instance

`docker-compose -p <name> up afl-libjpeg-main`
