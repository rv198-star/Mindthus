# INVALID PRESTART: host-reaped runner

This directory contains two local expansion prestarts that wrote prompt files
but produced no model response, event, stderr error, or provider signal. The
background subprocess was reclaimed by the host before an API call completed.

It is not an experimental result and is excluded from repeat 1. The actual
repeat-1 expansion was rerun in the sibling `v04-expansion/` directory through
a persistent TTY session and is the only scored expansion artifact.
