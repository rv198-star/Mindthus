# Incident-plan history

- Attempt 1 added a timeout retry and failed.
- A new runtime trace now proves that producer version 3 sends `user_id` while the
  consumer requires `userId`.
- A failing contract test reproduces this exact mismatch before any retry occurs.
