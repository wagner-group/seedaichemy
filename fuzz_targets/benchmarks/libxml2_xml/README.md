## 🧱 Step 1: Build the Docker Image

Build your fuzzing image using:

```bash
docker build -t <your-image-name> .
```

## Step 2: compile fuzzer with build.sh

```bash
docker run --rm \
  --user $(id -u):$(id -g) \
  -v $(pwd)/seeds:/seeds \
  -v $(pwd)/out:/out \
  <your-image-name> \
  bash -c "cd /src && ./build.sh"
```
## Step 3: run afl-fuzzing

```bash
docker run --rm -it \
  -v $(pwd)/seeds:/seeds \
  -v $(pwd)/out:/out \
  <your-image-name> \
  afl-fuzz -i /seeds -o /out -m none -- /out/<fuzz_target_binary> @@
```

## Optional:Remove /out
docker run --rm -v $(pwd):/mnt ubuntu bash -c "rm -rf /mnt/out"
mkdir out

