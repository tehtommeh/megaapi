# ASR with Parakeet

Example how to run:

```
docker build . --build-context shared=../shared -t megaapi/asr-parakeet

docker run --rm -p 8000:8000 --gpus=all -v ~/repos/parakeet-tdt-0.6b-v2/models--nvidia--parakeet-tdt-0.6b-v2:/root/.cache/huggingface/hub/models--nvidia--parakeet-tdt-0.6b-v2 docker.io/megaapi/asr-parakeet
```