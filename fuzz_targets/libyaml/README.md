To build the docker
```
docker build -t afl-libyaml .
```

To run the docker
```
docker run -it --rm \
  -v "$(pwd)/corpus:/input" \
  -v "$(pwd)/crash:/output" \
  afl-libyaml
```

Or
```
docker run -it --rm \
  -v "$(pwd)/corpus:/input" \
  -v "$(pwd)/crash:/output" \
  -u $(id -u):$(id -g) \
  afl-libyaml
  ```

Use 
```
rm -rf ./crash
```
to remove the crash folder (for a clean start).