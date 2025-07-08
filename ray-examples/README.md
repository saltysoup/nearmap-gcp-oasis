# Instructions

1. Deploy ray cluster with kubectl apply -f ray-cluster-a3ultra.yaml 
2. Wait until head pod and GPU VMs are deployed (takes upto 10 min)
2.1 Use kubectl describe raycluster and kubectl describe provreq to confirm DWS provisioning working
3. Once all pods are ready including GPU worker nodes, set up tunneling with local env with kubectl ray session pytorch-mnist-cluster &
4. Run example job with
```
ray job submit   --address http://localhost:8265   --runtime-env runtime-env.yaml   --working-dir .   -- python test_nccl_rdma.py
```

### A3 Ultra VMs have 3200 Gbps for GPU to GPU networking, so expect 350-400GB/s bandwidth for NCCL AG/AR with 4GiB/8GiB message size

ray job submit   --address http://localhost:8265   --runtime-env runtime-env.yaml   --working-dir .   -- python test_nccl_rdma.py
Job submission server address: http://localhost:8265
2025-07-08 07:11:28,447 INFO dashboard_sdk.py:338 -- Uploading package gcs://_ray_pkg_db951249fd2c9ce2.zip.
2025-07-08 07:11:28,448 INFO packaging.py:588 -- Creating a file package for local module '.'.
2025-07-08 07:11:29,729 INFO dashboard_sdk.py:385 -- Package gcs://_ray_pkg_db951249fd2c9ce2.zip already exists, skipping upload.

-------------------------------------------------------
Job 'raysubmit_UCt5UW3vXzr1v5Hy' submitted successfully
-------------------------------------------------------

Next steps
  Query the logs of the job:
    ray job logs raysubmit_UCt5UW3vXzr1v5Hy
  Query the status of the job:
    ray job status raysubmit_UCt5UW3vXzr1v5Hy
  Request the job to be stopped:
    ray job stop raysubmit_UCt5UW3vXzr1v5Hy

Tailing logs until the job exits (disable with --no-wait):
2025-07-08 00:11:30,260 INFO job_manager.py:531 -- Runtime env is setting up.
2025-07-08 00:11:33,157 INFO worker.py:1588 -- Using address 10.52.5.19:6379 set in the environment variable RAY_ADDRESS
2025-07-08 00:11:33,159 INFO worker.py:1723 -- Connecting to existing Ray cluster at address: 10.52.5.19:6379...
2025-07-08 00:11:33,173 INFO worker.py:1908 -- Connected to Ray cluster. View the dashboard at 10.52.5.19:8265 
All workers initialized. Starting benchmark...
(P2PWorker pid=10243, ip=10.52.2.7) [Rank 1] Ready.
(raylet) It looks like you're creating a detached actor in an anonymous namespace. In order to access this actor in the future, you will need to explicitly connect to this namespace with ray.init(namespace="04986c52-f3a0-4ba7-9fe8-7e08ddd23f53", ...)

==================================================
 NCCL Bi-Directional Point-to-Point Benchmark
==================================================
  Message Size: 4 GB
  Iterations: 10
--------------------------------------------------
  Bandwidth (0 -> 1): 2979.26 Gbps (372.41 GB/s)
  Bandwidth (1 -> 0): 2972.62 Gbps (371.58 GB/s)
--------------------------------------------------
  Average Bandwidth: 2975.94 Gbps (371.99 GB/s)
==================================================

(P2PWorker pid=10242, ip=10.52.2.7) [Rank 0] Ready.

------------------------------------------
Job 'raysubmit_UCt5UW3vXzr1v5Hy' succeeded
------------------------------------------
