## 🧱 Step 1: Build the Docker Image

Build your fuzzing image using:

```bash
docker build -t <your-base-image-name> .
```

## Step 2: compile fuzzer with build.sh

```bash
docker build \
  -f Dockerfile.extended \
  --build-arg BASE_IMAGE=<your-base-image-name> \
  -t <program_folder_name>_fuzz_ready .
```
example: for libpcap/ dir use ...-t libpcap_fuzz_ready
**Optional**
if you use different docker image name for final docker image, you will need to go into docker-compose.yaml and change image: parameter.
## Step 3: run afl-fuzzing

```bash
# Running in detached mode is recommended
docker-compose -p <name> run afl-<program_folder_name>-main
```
again you will need to go into docker-compose.yaml to change program name if you want to use different name for afl-<program_folder_name>-main

for detach mode:
```bash
docker-compose -p <name> up -d afl-<program_folder_name>-main
```

**Alternative running method** 
```bash
COMPOSE_PROJECT_NAME=<name> docker-compose up --build -d
```
Inspect Cotainer log:
```bash
docker logs <container-name-or-id>
```
## Optional:Remove /out
```bash
docker run --rm -v $(pwd):/mnt ubuntu bash -c "rm -rf /mnt/out"
mkdir out
```

## Inspect crashes and fuzzing output
```bash
docker run --rm -v $(pwd)/out:/mnt ubuntu bash -c "chown -R $(id -u):$(id -g) /mnt"
```
```bash
ls -l out/default
```
