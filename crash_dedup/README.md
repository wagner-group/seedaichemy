This is a standalone script to deduplicate and identify unique crashes from a afl fuzz docker instance for a program in fuzz_targets. Working for lcms, but let me know if not working for other programs

To run this tool:

### 1.

Update the docker-compose.yaml. Specifically, update the name of the output volume and the target program binary directory inside that volume.

### 2.

`docker compose up --build`
