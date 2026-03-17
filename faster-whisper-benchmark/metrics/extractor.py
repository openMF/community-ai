import numpy as np


def us_to_ms(x):
    return x / 1e3

def bytes_to_mb(x):
    return x / (1024 ** 2)

def extract_metrics_from_profile(profile: dict):
    exec_sum    = profile.get("execution_summary", {})
    exec_detail = profile.get("execution_detail", [])

    # ── End-to-End Performance ────────────────────────────────────
    times      = np.array(exec_sum.get("all_inference_times", []))
    first_load = exec_sum.get("first_load_time", 0)
    warm_load  = exec_sum.get("warm_load_time", 0)

    metrics = {
        "estimated_inference_time_ms": round(us_to_ms(exec_sum.get("estimated_inference_time", 0)), 4),
        "mean_latency_ms":    round(us_to_ms(times.mean()), 4)             if len(times) else None,
        "min_latency_ms":     round(us_to_ms(times.min()), 4)              if len(times) else None,
        "max_latency_ms":     round(us_to_ms(times.max()), 4)              if len(times) else None,
        "std_dev_ms":         round(us_to_ms(times.std()), 4)              if len(times) else None,
        "coeff_of_variation": round((times.std() / times.mean()) * 100, 4) if len(times) else None,
        "throughput_fps":     round(1000 / us_to_ms(times.mean()), 4)      if len(times) else None,
        "cold_start_ms":      round(us_to_ms(first_load), 4),
        "warm_start_ms":      round(us_to_ms(warm_load), 4),
        "speedup_cold_warm":  round(first_load / warm_load, 4) if warm_load else None,
    }

    # ── Memory Footprint ──────────────────────────────────────────
    inf_mem  = exec_sum.get("estimated_inference_peak_memory", 0)
    cold_mem = exec_sum.get("first_load_peak_memory", 0)
    warm_mem = exec_sum.get("warm_load_peak_memory", 0)

    metrics.update({
        "estimated_inference_peak_memory": round(bytes_to_mb(inf_mem), 4),
        "cold_start_peak_mb":             round(bytes_to_mb(cold_mem), 4),
        "warm_start_peak_mb":             round(bytes_to_mb(warm_mem), 4),
        "memory_reduction_cold_warm_pct": round((1 - warm_mem / cold_mem) * 100, 4) if cold_mem else None,
        "memory_reduction_warm_inf_pct":  round((1 - inf_mem / warm_mem) * 100, 4)  if warm_mem else None,
        "memory_efficiency_ratio":        round(inf_mem / cold_mem, 4)              if cold_mem else None,
    })

    # ── Accelerator Utilization ───────────────────────────────────
    if exec_detail:
        total_time      = sum(op.get("execution_time", 0) for op in exec_detail)
        total_op_count  = len(exec_detail)
        zero_op_count   = sum(1 for op in exec_detail if op.get("execution_time", 0) == 0)
        nonzero_op_count = total_op_count - zero_op_count

        unit_times = {}
        for op in exec_detail:
            unit = op.get("compute_unit", "UNKNOWN")
            unit_times[unit] = unit_times.get(unit, 0) + op.get("execution_time", 0)

        metrics.update({
            "total_op_count":          total_op_count,
            "nonzero_op_count":        nonzero_op_count,
            "zero_op_count":           zero_op_count,
            "zero_op_percentage":      round(zero_op_count / total_op_count * 100, 4) if total_op_count else 0.0,
            "avg_op_time_ms":          round(us_to_ms(total_time / nonzero_op_count), 4) if nonzero_op_count else 0.0,
            "total_op_time_ms":        round(us_to_ms(total_time), 4),
            "dominant_compute_unit":   max(unit_times, key=unit_times.get) if unit_times else "N/A",
            "cpu_utilization_percentage": round(unit_times.get("CPU", 0.0) / total_time * 100, 4) if total_time else 0.0,
            "gpu_utilization_percentage": round(unit_times.get("GPU", 0.0) / total_time * 100, 4) if total_time else 0.0,
            "npu_utilization_percentage": round(unit_times.get("NPU", 0.0) / total_time * 100, 4) if total_time else 0.0,
        })

        # ── Performance Bottlenecks ───────────────────────────────
        top_ops       = sorted(exec_detail, key=lambda op: op.get("execution_time", 0), reverse=True)[:15]
        top_ops_total = sum(op.get("execution_time", 0) for op in top_ops)

        metrics.update({
            "top15_ops_time_ms":        round(us_to_ms(top_ops_total), 4),
            "top15_ops_pct_of_total":   round(top_ops_total / total_time * 100, 4) if total_time else 0.0,
            "effective_op_time_ratio":  round(top_ops_total / total_time, 4)        if total_time else 0.0,
        })

    return {k: v for k, v in metrics.items() if v is not None}
