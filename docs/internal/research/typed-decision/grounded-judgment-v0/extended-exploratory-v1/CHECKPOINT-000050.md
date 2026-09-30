# Second continuation checkpoint — 50 calls

Owner approved 000047 risk acceptance and bounded budget flexibility. Named continuation source 02687f24f289f9ed9ae9d65d1138dd39bc921d91; prior 48 calls and unknown retained; no replay or reset. New B atoms for reported record returned with reported origin and a limit finding, but its host draft then lost the stream.

New call 000049 / record-source-2-B:1 / request 0817e559b299453a5902667c85da2e69ec5b3280eb0bee4c66d0b2d35b4a800a has CLI thread 01a0f279-8047-7521-9a0b-eb97737c8a72. CLI emitted turn.failed with ordinary message `stream disconnected before completion: idle timeout waiting for SSE` and no structured failure code. Local CLI session 343.275067 seconds, returncode 1, no reply. This is distinct from the previous subprocess TimeoutExpired and does not prove remote generation finished. classify correctly preserves unknown; STOP-000049 remains.

Current 24 paths: 12 delivered, 2 format failures, 2 unknown (000047 risk accepted; 000049 pending disposition), 8 not sent. 50 logical calls = 35 host + 15 Jev. No retries/review-model calls; original caps remain 176/144/32, within budget. There is no new safety refusal. [Original second failure](failures/000049/raw.json) and [binding/terminal](failures/000049/terminal.json) remain accessible.

A narrowly bounded additional-risk proposal has been sent to Owner; no execution dependent on it occurs before confirmation. No local timeout/configuration change is implemented. The earlier user-facing description of another local six-minute timeout was corrected after reading the actual CLI stream events. Do not write this as a pure local timeout or known remote completion.
