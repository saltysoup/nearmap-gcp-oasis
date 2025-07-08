import os
import ray
import time
import cupy as cp
import argparse
from ray.util.collective.types import Backend
import ray.util.collective as collective

GROUP = "p2p_benchmark_group"

@ray.remote(num_gpus=1)
class P2PWorker:
    def __init__(self, world_size: int, rank: int, tensor_gb: int):
        self.rank = rank
        self.world_size = world_size
        self.tensor_size_bytes = tensor_gb * 1024 * 1024 * 1024

        collective.init_collective_group(
            world_size=self.world_size,
            rank=self.rank,
            backend=Backend.NCCL,
            group_name=GROUP,
        )

    def ready(self):
        """Simple method to check if the actor is initialized."""
        print(f"[Rank {self.rank}] Ready.")
        return True

    def run_benchmark(self, num_iterations=10, direction="send_first"):
        """Runs a timed benchmark for a given direction."""
        tensor = cp.ones(self.tensor_size_bytes, dtype=cp.uint8)
        
        # Determine sender and receiver
        sender_rank, receiver_rank = (0, 1) if direction == "send_first" else (1, 0)
        
        # Warm-up
        for _ in range(5):
            if self.rank == sender_rank:
                collective.send(tensor, dst_rank=receiver_rank, group_name=GROUP)
            elif self.rank == receiver_rank:
                collective.recv(tensor, src_rank=sender_rank, group_name=GROUP)
        cp.cuda.Stream.null.synchronize()
        
        # Timed benchmark
        start_time = time.time()
        for _ in range(num_iterations):
            if self.rank == sender_rank:
                collective.send(tensor, dst_rank=receiver_rank, group_name=GROUP)
            elif self.rank == receiver_rank:
                collective.recv(tensor, src_rank=sender_rank, group_name=GROUP)
        cp.cuda.Stream.null.synchronize()
        duration = time.time() - start_time
        
        # The sender calculates and returns the bandwidth
        if self.rank == sender_rank:
            avg_time = duration / num_iterations
            bandwidth_gbps = (self.tensor_size_bytes * 8) / (avg_time * 1e9)
            bandwidth_gbs = self.tensor_size_bytes / (avg_time * 1e9)
            return (bandwidth_gbps, bandwidth_gbs)
        
        return None

    def shutdown(self):
        collective.destroy_collective_group(GROUP)

def main():
    parser = argparse.ArgumentParser(description="NCCL Point-to-Point Benchmark")
    parser.add_argument("--num-nodes", type=int, default=2, help="Number of nodes to use for the test.")
    parser.add_argument("--iterations", type=int, default=10, help="Number of timed iterations.")
    parser.add_argument("--tensor-gb", type=int, default=4, help="Tensor size in Gigabytes (GB).")
    args = parser.parse_args()

    if args.num_nodes != 2:
        raise ValueError("This script is designed for exactly two nodes.")

    ray.init(address="auto")
    
    workers = [
        P2PWorker.options(num_gpus=1).remote(args.num_nodes, rank=i, tensor_gb=args.tensor_gb)
        for i in range(args.num_nodes)
    ]

    # 1. Ensure all workers are initialized before starting
    ray.get([w.ready.remote() for w in workers])
    print("All workers initialized. Starting benchmark...")

    # 2. Run benchmark in direction 0 -> 1
    results_0_to_1 = ray.get([w.run_benchmark.remote(args.iterations, "send_first") for w in workers])
    bw_0_to_1 = next(res for res in results_0_to_1 if res is not None)

    # 3. Run benchmark in direction 1 -> 0
    results_1_to_0 = ray.get([w.run_benchmark.remote(args.iterations, "recv_first") for w in workers])
    bw_1_to_0 = next(res for res in results_1_to_0 if res is not None)
    
    # --- Print Results ---
    print("\n" + "="*50)
    print(" NCCL Bi-Directional Point-to-Point Benchmark")
    print("="*50)
    print(f"  Message Size: {args.tensor_gb} GB")
    print(f"  Iterations: {args.iterations}")
    print("-" * 50)
    print(f"  Bandwidth (0 -> 1): {bw_0_to_1[0]:.2f} Gbps ({bw_0_to_1[1]:.2f} GB/s)")
    print(f"  Bandwidth (1 -> 0): {bw_1_to_0[0]:.2f} Gbps ({bw_1_to_0[1]:.2f} GB/s)")
    print("-" * 50)
    avg_gbps = (bw_0_to_1[0] + bw_1_to_0[0]) / 2
    avg_gbs = (bw_0_to_1[1] + bw_1_to_0[1]) / 2
    print(f"  Average Bandwidth: {avg_gbps:.2f} Gbps ({avg_gbs:.2f} GB/s)")
    print("="*50 + "\n")

    ray.get([w.shutdown.remote() for w in workers])

if __name__ == "__main__":
    main()
