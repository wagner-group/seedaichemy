This is a testing suite for evaluating a test corpus by running afl-fuzz on the mutool command from the mupdf project. 

## Building and Running with Docker

### 0. (optional) Build the Docker image :
```bash
docker build -t fuzz-testing .
# or if updating the existing image,
docker build -t fuzz-testing . --no-cache
```
You only need to do this step if you are running on something other than the red5k server. For that server I've already built the image. You can also run this if there are some issues with the build/you want to modify anything. I also think you have to modify this if you make any changes to the entrypoint. In those cases please rename "fuzz-testing" in the command to a different name of your choice, or it will overwrite the previous image.

This will create a docker image called "fuzz-testing". Running the command will be rather lengthy at the first run, but will cashe for future runs. 

### 1. Copy test corpus into /corpus

If this would take too long, see step two. otherwise, skip to step three.

### 2. (optional) Modify the docker-compose.yaml

By default the script looks for the corpus in a directory called "/corpus" and puts the output in a directory "/afl-output". this can be changed by modifying the docker-compose.yaml section called volumes. Additionally, the program takes in a few environment variables to determine some parameters for the afl call within the docker container.  These can also be modified in the same folder. You likely don't need to touch these.

### 3. Set output file permissions
Run
```bash
chmod -R 777 afl-output
```
Or replace that with your desired output folder

### 4. Running and stopping the Docker instance:

IMPORTANT: Make sure to replace [name] with a unique name that no one else is using, otherwise there may be conflicts. -p <name> serves to define a project name. Using your own name plus a title is probably a good idea. To be safe you should likely run docker ps -a to check what has been already used. This [name] variable will be combined with a few other variables to make a name for the docker container you are running, ie. [name]-afl-mupdf

```bash
# Running in detached mode is recommended
docker-compose -p <name> up afl-mupdf-main
```
or
```bash
docker-compose -p <name> up -d afl-mupdf-main
```
to run in detached mode. To view information in detached mode, you can use these commands:


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
docker logs --since "2025-04-26T05:40:21" karen-3-afl-mupdf | head -n 25
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
```

### 4a. Running secondary instances
After the master instance is launched you can run the following commands:
```bash
# Start 3 secondary instances
docker-compose -p <name> up -d --scale afl-secondary=3
```
You can also run this in lieu of the original command, and it will start a master instance on its own. But keep in mind that if afl++ is warning about slow execution speed it can be a solution to add additional instances; you don't have to run this as the first command.

### 4b. Stopping the fuzzing
```bash
docker-compose -p <name> down -v
```
Make sure to use the same project name in this command. Note that this version of the command will remove the volume, so make sure to copy or analyze your data before you're done with that. If you want to preserve the volume, use
```bash
docker-compose -p <name> down
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


### 5. Reading a volume
```bash
docker run --rm -it \
  -v [volume-name]:/data \
  aflplusplus/aflplusplus:latest \
  /bin/bash
```
The data will be in /data. Note that the volume name will be different from the project name. by default it should append "_output-volume".

Here are some useful commands you can run from that /data folder. These even work when using multiple instances:
```bash
# Status check tool, -s combines outputs from multiple instances.
afl-whatsup -s .
```

You can list active volumes with the following docker command:
```bash
docker volume ls
```

## Run AFL corpus minimizer

### 1. Copy test corpus into /corpus

If this would take too long, you can modify the mounted volume destination in docker-compose.yaml

### 2. Create output directory to store minmized corpus
(optional) you can delete existed corpus_min directory using 
Run
```bash
rm -rf corpus_min
```

Run
```bash
mkdir -p corpus_min
chmod -R 777 corpus_min
```

### 3. Run the container:
```bash
docker-compose -p [name] run --rm afl-mupdf-main minimize draw @@
```

Note: You may see permissions related errors when running this command, even if this happens the program may still be working properly. You can verify this by checking the corpus minimization folder "corpus_min".

## General Info and Debugging

If you want to examine the names that other people are using, you can run

```bash
docker ps -a
```




