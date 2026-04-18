from __future__ import annotations

import argparse
import math
import os
import shlex
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable


def sh(
    cmd: list[str], env: dict[str, str] | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, env=env, text=True, capture_output=True, check=check)


def run_streaming(cmd: list[str], env: dict[str, str] | None = None) -> int:
    print(f"\n[cmd] {' '.join(shlex.quote(x) for x in cmd)}", flush=True)
    proc = subprocess.Popen(cmd, env=env)
    return proc.wait()


def run_with_retries(
    cmd: list[str],
    env: dict[str, str],
    retries: int,
    retry_backoff_s: float,
    label: str,
) -> None:
    attempt = 0
    while True:
        attempt += 1
        rc = run_streaming(cmd, env=env)
        if rc == 0:
            return
        if attempt > retries:
            raise RuntimeError(
                f"{label} failed after {retries + 1} attempts with return code {rc}"
            )
        sleep_s = retry_backoff_s * (2 ** (attempt - 1))
        print(
            f"[retry] {label} failed with rc={rc}, sleeping {sleep_s:.1f}s", flush=True
        )
        time.sleep(sleep_s)


def query_nvidia_smi(
    fields: list[str], gpu_uuid: str | None = None
) -> list[dict[str, str]]:
    cmd = ["nvidia-smi"]
    if gpu_uuid:
        cmd += ["--id=" + gpu_uuid]
    cmd += [
        f"--query-gpu={','.join(fields)}",
        "--format=csv,noheader,nounits",
    ]
    out = sh(cmd).stdout.strip().splitlines()
    rows = []
    for line in out:
        vals = [x.strip() for x in line.split(",")]
        rows.append(dict(zip(fields, vals)))
    return rows


def get_default_gpu_uuid() -> str:
    rows = query_nvidia_smi(["gpu_uuid"])
    if not rows:
        raise RuntimeError("No GPU found via nvidia-smi")
    return rows[0]["gpu_uuid"]


def get_gpu_total_memory_mb(gpu_uuid: str) -> int:
    rows = query_nvidia_smi(["memory.total"], gpu_uuid=gpu_uuid)
    return int(rows[0]["memory.total"])


def get_gpu_memory_used_mb(gpu_uuid: str) -> int:
    rows = query_nvidia_smi(["memory.used"], gpu_uuid=gpu_uuid)
    return int(rows[0]["memory.used"])


def build_base_env(
    gpu_uuid: str,
    torch_num_threads: int,
    torch_num_interop_threads: int,
) -> dict[str, str]:
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = gpu_uuid
    env["TORCH_NUM_THREADS"] = str(torch_num_threads)
    env["TORCH_NUM_INTEROP_THREADS"] = str(torch_num_interop_threads)
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["NUMEXPR_NUM_THREADS"] = "1"
    env.setdefault("WANDB_START_METHOD", "thread")
    return env


@contextmanager
def mps_daemon(enabled: bool, env: dict[str, str]):
    if not enabled:
        yield env
        return

    pipe_dir = tempfile.mkdtemp(prefix=f"nvidia-mps-pipe-{os.getpid()}-")
    log_dir = tempfile.mkdtemp(prefix=f"nvidia-mps-log-{os.getpid()}-")
    mps_env = env.copy()
    mps_env["CUDA_MPS_PIPE_DIRECTORY"] = pipe_dir
    mps_env["CUDA_MPS_LOG_DIRECTORY"] = log_dir

    print(f"[mps] pipe={pipe_dir}")
    print(f"[mps] log={log_dir}")
    subprocess.check_call(["nvidia-cuda-mps-control", "-d"], env=mps_env)

    try:
        yield mps_env
    finally:
        try:
            p = subprocess.Popen(
                ["nvidia-cuda-mps-control"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                env=mps_env,
            )
            p.communicate("quit\n", timeout=5)
        except Exception:
            pass


def sample_peak_gpu_memory_used_mb(
    gpu_uuid: str,
    proc: subprocess.Popen,
    sample_interval_s: float,
    settle_delay_s: float,
) -> tuple[int, int, list[int]]:
    baseline = get_gpu_memory_used_mb(gpu_uuid)
    peak = baseline
    samples = [baseline]

    if settle_delay_s > 0:
        time.sleep(settle_delay_s)

    while proc.poll() is None:
        used = get_gpu_memory_used_mb(gpu_uuid)
        samples.append(used)
        peak = max(peak, used)
        time.sleep(sample_interval_s)

    used = get_gpu_memory_used_mb(gpu_uuid)
    samples.append(used)
    peak = max(peak, used)
    delta_peak = max(1, peak - baseline)
    return baseline, delta_peak, samples


def probe_peak_memory_mb_external(
    train_script: str,
    env: dict[str, str],
    base_overrides: list[str],
    probe_seed: int,
    probe_max_epochs: int,
    probe_extra_overrides: list[str],
    sample_interval_s: float,
    settle_delay_s: float,
) -> float:
    cmd = [
        sys.executable,
        train_script,
        f"seed={probe_seed}",
        *base_overrides,
        *probe_extra_overrides,
        f"trainer.max_epochs={probe_max_epochs}",
    ]
    print(f"\n[probe] launching {' '.join(shlex.quote(x) for x in cmd)}", flush=True)

    probe_env = env.copy()
    # hard off: nothing initializes
    # probe_env["WANDB_DISABLED"] = "true"
    # or, if you prefer offline local logging only:
    probe_env["WANDB_MODE"] = "offline"

    proc = subprocess.Popen(cmd, env=env)
    baseline_mb, peak_delta_mb, _samples = sample_peak_gpu_memory_used_mb(
        gpu_uuid=env["CUDA_VISIBLE_DEVICES"],
        proc=proc,
        sample_interval_s=sample_interval_s,
        settle_delay_s=settle_delay_s,
    )
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"Probe run failed with rc={rc}")
    print(
        f"[probe] baseline_mb={baseline_mb} delta_peak_mb={peak_delta_mb}", flush=True
    )
    return float(peak_delta_mb)


def chunked(xs: list[int], n: int) -> Iterable[list[int]]:
    for i in range(0, len(xs), n):
        yield xs[i : i + n]


def launch_seed_batch(
    train_script: str,
    env: dict[str, str],
    seeds: list[int],
    base_overrides: list[str],
    retries: int,
    retry_backoff_s: float,
) -> None:
    active = len(seeds)
    batch_env = env.copy()
    batch_env["CUDA_MPS_ACTIVE_THREAD_PERCENTAGE"] = str(max(1, 100 // active))

    seed_csv = ",".join(str(s) for s in seeds)
    cmd = [
        sys.executable,
        train_script,
        "--multirun",
        "hydra/launcher=joblib",
        f"hydra.launcher.n_jobs={active}",
        f"hydra.launcher.pre_dispatch={active}",
        f"seed={seed_csv}",
        *base_overrides,
    ]

    label = f"batch seeds={seed_csv}"
    try:
        run_with_retries(
            cmd,
            batch_env,
            retries=retries,
            retry_backoff_s=retry_backoff_s,
            label=label,
        )
    except Exception:
        if active == 1:
            raise
        print(
            "[fallback] batch failed permanently, retrying each seed independently",
            flush=True,
        )
        for seed in seeds:
            single_env = env.copy()
            single_env["CUDA_MPS_ACTIVE_THREAD_PERCENTAGE"] = "100"
            single_cmd = [
                sys.executable,
                train_script,
                f"seed={seed}",
                *base_overrides,
            ]
            run_with_retries(
                single_cmd,
                single_env,
                retries=retries,
                retry_backoff_s=retry_backoff_s,
                label=f"seed={seed}",
            )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--train-script", default="train.py")
    p.add_argument("--gpu-uuid", default=None)
    p.add_argument("--num-seeds", type=int, required=True)
    p.add_argument("--base-seed", type=int, default=1000)
    p.add_argument("--probe-seed", type=int, default=123)
    p.add_argument("--probe-max-epochs", type=int, default=1)
    p.add_argument(
        "--probe-extra-overrides",
        type=str,
        nargs="*",
        default=[],
        help="Extra Hydra overrides applied only to the probe run",
    )
    p.add_argument(
        "--variants",
        type=str,
        nargs="*",
        default=[],
        metavar="OVERRIDE",
        help="Each value is an extra Hydra override defining one experiment variant. "
        "Seeds are run for every variant. Example: "
        "'datamodule.noise_std_temp=0.0' 'datamodule.noise_std_temp=0.5'",
    )
    p.add_argument("--safety-factor", type=float, default=1.5)
    p.add_argument("--gpu-headroom-mb", type=int, default=1024)
    p.add_argument("--reserve-cpus", type=int, default=1)
    p.add_argument("--max-jobs", type=int, default=0)
    p.add_argument("--torch-num-threads", type=int, default=1)
    p.add_argument("--torch-num-interop-threads", type=int, default=1)
    p.add_argument("--sample-interval-s", type=float, default=0.2)
    p.add_argument("--settle-delay-s", type=float, default=1.0)
    p.add_argument("--retries", type=int, default=1)
    p.add_argument("--retry-backoff-s", type=float, default=20.0)
    p.add_argument("--disable-mps", action="store_true")
    p.add_argument(
        "overrides",
        nargs=argparse.REMAINDER,
        help="Hydra overrides passed through to the training script. Prefix with --",
    )
    args = p.parse_args()

    # Each variant is a list of overrides to add on top of base_overrides
    variants: list[list[str]] = [[v] for v in args.variants] if args.variants else [[]]

    base_overrides = list(args.overrides)
    if base_overrides and base_overrides[0] == "--":
        base_overrides = base_overrides[1:]

    gpu_uuid = args.gpu_uuid or get_default_gpu_uuid()
    gpu_total_mb = get_gpu_total_memory_mb(gpu_uuid)
    n_cpu = os.cpu_count() or 1

    base_env = build_base_env(
        gpu_uuid=gpu_uuid,
        torch_num_threads=args.torch_num_threads,
        torch_num_interop_threads=args.torch_num_interop_threads,
    )

    with mps_daemon(enabled=not args.disable_mps, env=base_env) as env:
        peak_mb = probe_peak_memory_mb_external(
            train_script=args.train_script,
            env=env,
            base_overrides=base_overrides,
            probe_seed=args.probe_seed,
            probe_max_epochs=args.probe_max_epochs,
            probe_extra_overrides=args.probe_extra_overrides,
            sample_interval_s=args.sample_interval_s,
            settle_delay_s=args.settle_delay_s,
        )

        per_job_mb = max(1, math.ceil(peak_mb * args.safety_factor))
        usable_gpu_mb = max(1, gpu_total_mb - args.gpu_headroom_mb)
        fit_by_mem = max(1, usable_gpu_mb // per_job_mb)
        fit_by_cpu = max(1, n_cpu - args.reserve_cpus)

        n_jobs = min(fit_by_mem, fit_by_cpu)
        if args.max_jobs > 0:
            n_jobs = min(n_jobs, args.max_jobs)

        seeds = [args.base_seed + i for i in range(args.num_seeds)]

        print("\n[plan]")
        print(f"gpu_uuid={gpu_uuid}")
        print(f"gpu_total_mb={gpu_total_mb}")
        print(f"probe_peak_mb_external={peak_mb:.1f}")
        print(f"per_job_mb={per_job_mb}")
        print(f"usable_gpu_mb={usable_gpu_mb}")
        print(f"n_cpu={n_cpu}")
        print(f"fit_by_mem={fit_by_mem}")
        print(f"fit_by_cpu={fit_by_cpu}")
        print(f"n_jobs={n_jobs}")
        print(f"num_seeds={len(seeds)}")
        print(f"variants={len(variants)} (each with {len(seeds)} seeds)")

        for variant_overrides in variants:
            combined_overrides = base_overrides + variant_overrides
            label = " ".join(variant_overrides) or "default"
            print(f"\n[variant] {label}", flush=True)

            for i, batch in enumerate(chunked(seeds, n_jobs), start=1):
                print(f"\n[batch {i}] seeds={batch} variant={label}", flush=True)
                launch_seed_batch(
                    train_script=args.train_script,
                    env=env,
                    seeds=batch,
                    base_overrides=combined_overrides,
                    retries=args.retries,
                    retry_backoff_s=args.retry_backoff_s,
                )

        # for i, batch in enumerate(chunked(seeds, n_jobs), start=1):
        #     print(f"\n[batch {i}] seeds={batch}", flush=True)
        #     launch_seed_batch(
        #         train_script=args.train_script,
        #         env=env,
        #         seeds=batch,
        #         base_overrides=base_overrides,
        #         retries=args.retries,
        #         retry_backoff_s=args.retry_backoff_s,
        #     )

    print("\n[done] all batches completed", flush=True)


if __name__ == "__main__":
    main()
