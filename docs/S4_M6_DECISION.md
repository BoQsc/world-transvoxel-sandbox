# S4 M6 Decision

S4 status: complete.

Decision: CPU/native retained; compute rejected for now.

Command:

```console
python tools/s4_m6_decision.py
```

Expected marker:

```text
WT_SANDBOX_S4_M6_DECISION_PASS decision=cpu_native_retained_compute_rejected_for_now
```

## Decision basis

S4 selected interactive edit-settle latency from S3 evidence, then ran
`tools/s4_cpu_edit_phase_baseline.py` to attribute the CPU/native path.

The baseline found:

- max total measured edit cycle: 1205 ms;
- max sample capture: 149 ms;
- max transaction submission: 1 ms;
- max commit/journal/replacement publication: 27 ms;
- max edit replacement mesh completion: 38 ms;
- max render queue/resource readiness: 134 ms;
- max collision queue/resource readiness: 0 ms;
- max final stable-settle hold: 857 ms.

The compute-relevant maximum is 149 ms, below the 250 ms investigation floor.
The largest time is the explicit stable-settle hold, which is a correctness
quiet-window gate, not a compute workload.

## Outcome

S4 exits with the CPU/native path retained. No S4 compute prototype is
authorized.

This is not a permanent ban on compute. Reopen compute only when a later
workload shows a measured terrain source, meshing, render-upload, collision, or
transfer/readback bottleneck that a targeted compute path can improve end to
end while keeping deterministic CPU/headless fallback.

## Still out of scope

- broad GPU rewrite;
- removing deterministic CPU/headless fallback;
- water/lava, planets, structural stability, game repository, or 0BSD backend
  replacement.
