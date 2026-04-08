import logging
import subprocess

logger = logging.getLogger(__name__)


def get_gpu_metrics() -> dict:
    metrics = {
        "gpu_name": None,
        "gpu_util_percent": None,
        "gpu_memory_util_percent": None,
        "vram_used_gb": None,
        "vram_total_gb": None,
        "gpu_available": False,
    }

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,utilization.memory,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            first_row = result.stdout.strip().splitlines()[0]
            parts = [part.strip() for part in first_row.split(",")]
            if len(parts) >= 5:
                gpu_name, gpu_util, gpu_mem_util, mem_used_mb, mem_total_mb = parts[:5]
                metrics.update(
                    {
                        "gpu_name": gpu_name,
                        "gpu_util_percent": round(float(gpu_util), 1),
                        "gpu_memory_util_percent": round(float(gpu_mem_util), 1),
                        "vram_used_gb": round(float(mem_used_mb) / 1024.0, 2),
                        "vram_total_gb": round(float(mem_total_mb) / 1024.0, 1),
                        "gpu_available": True,
                    }
                )
                return metrics
    except Exception as e:
        logger.debug(f"nvidia-smi metric okunamadi: {e}")

    try:
        import torch

        if torch.cuda.is_available():
            metrics.update(
                {
                    "gpu_name": torch.cuda.get_device_name(0),
                    "vram_used_gb": round(torch.cuda.memory_allocated(0) / (1024**3), 2),
                    "vram_total_gb": round(
                        torch.cuda.get_device_properties(0).total_memory / (1024**3), 1
                    ),
                    "gpu_available": True,
                }
            )
    except Exception as e:
        logger.debug(f"torch cuda metric okunamadi: {e}")

    return metrics
