# AFL++ Fuzzing Template
This directory contains a template for running AFL++ with minimization on Docker. If you only want to run
the minimization script, skip to the [Minimization](#minimization) section.

## Building and running with Docker

### 0: Modify the template for the user application
1. Make a copy of `fuzz_template`, and rename it to the user specific application (ex. 'libpng').
2. Go to `Dockerfile` and compile the fuzz target. To do this, follow the instructions in the section labeled TODO. 
After compiling the fuzz target, assign `FUZZER_BIN` to the path of the compiled binary (ex. `FUZZER_BIN=/path/to/fuzz_target`).
3. Go to `docker-compose.yaml` and replace every `<application-name>` with the name of the user specific application (ex. 'libpng')

### 1: Build the Docker image :
```bash
docker build -t fuzz-<application-name> .
```
where `<application-name>` is the name of the user specific application (ex. 'libpng').

### 2. Load seed corpus files into ./corpus
If you are using the combination tool, see `fuzzing-for-llms/README.md`.

### 3. Running and stopping the Docker instance:

To run the Docker instance with minimization (default), use
```bash
docker compose -p <name> up afl-<application-name>-main
```
or
```bash
# Running in detached mode is recommended
docker compose -p <name> up -d afl-<application-name>-main
```
to run in detached mode. To run the Docker instance using the original seed corpus, use
```bash
docker compose -p <name> up afl-<application-name>-unmin
```
or
```bash
# Running in detached mode is recommended
docker compose -p <name> up -d afl-<application-name>-unmin
```

To view information in detached mode, you can use these commands:

```bash
# most recent afl interface
docker logs --tail 23 <container-id-or-name>
# for total logs
docker logs -f <container-id-or-name>
# or, for a single snapshot
docker logs <container-id-or-name>
# alternative command, it enters the instance
docker attach <container_id>
```

If you want to see the docker instance at a particular timestamp (you don't wanna sit there to see it hit the 24 hour mark), you can do
```bash
docker logs --since "TIME STAMP YOU WANT TO INSPECT" <container name of id> | head -n 25
```
For example,
```bash
docker logs --since "2025-04-26T05:40:21" ajoe-afl-libpng | head -n 25
```

Note: here's an easy way to get the 0 and 24-hour fuzzing results using the container id or name:
24-hour:
```bash
CID=<container id or name>

start=$(docker inspect -f '{{.State.StartedAt}}' "$CID")
echo "Started at: $start"

mark=$(date -d "$start +24 hours" --iso-8601=seconds)
echo "24-hour mark: $mark"

docker logs --since "$mark" $CID | head -n 25
```
using this timestamp and the method above will give you the twenty four hour.

Initial coverage/0th cycle cycle:
This command gives the fuzzing output for the first cycle, which should mean it's after every corpus item is run at least once
```bash
docker logs <container id or name> | grep -n -A10 -B15 "cycle progress" | head -n 50

### 5. Stopping the fuzzing
```bash
docker compose -p <name> down -v
```
Make sure to use the same project name in this command. Note that this version of the command will remove the volume, so make sure to 
copy or analyze your data before you're done with that. If you want to preserve the volume, use
```bash
docker compose -p <name> down
```
Please make sure to remove your volume manually later, as it can cause naming conflicts. This can be done with
```bash
# List the volume names
docker volume ls
# deletes specific volume
docker volume rm <volume-name>
```

if any of the above commands fail,you can also remove the containers manually
```bash
docker ps
```
or 
```bash
docker ps -a
```
will show the existing containers and names, and then you can use
```bash
docker stop <container_id>
docker rm <container_id>
```
to smoothly stop and remove the container.

## Minimization
The minimization logic is in `minimize.sh`. To minimize a corpus, run
```
./minimize.sh /path/to/corpus /path/to/minimized/corpus fuzz_target
```
where `fuzz_target` is an instrumented binary for AFL++. This is done automatically when you run `docker compose`, but you can also 
use the script in a different environment.