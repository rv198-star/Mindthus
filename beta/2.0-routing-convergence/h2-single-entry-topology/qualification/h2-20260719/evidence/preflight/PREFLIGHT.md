# H2 Live Preflight

- candidate commit: `9c271c1f3fb86f1e81f4860d32d9e5ac4f08b59c`
- release line/version: `2.0-routing-h2-single-entry` / `2.0.0-next.3`
- Codex: `codex-cli 0.144.4`
- model/effort: `gpt-5.6-sol` / `xhigh`
- candidate package tree digest: `31d6f58eab05c818b5b2d0acbdf6b6597eec5003123fe4cb3daf2a994dcbf0e0`
- plugin manifest digest: `b1e4f1567f29195ed895d551b820960b76516ab0bba23ec1672efc483c20a347`
- fixture-lock digest: `f5a3e305f068282beeb28caa7ee1713728a82b58067294311a59c6f780a092bb`
- copied Q7 workspace digest: `d40eecfd79ab2d81f8c57827a3c392b12f1c6874970d55ac8f66fc0fdb569192`
- isolated home: `/private/tmp/mindthus-h2-q-20260719-9c271c1f/home`
- candidate cache: `/private/tmp/mindthus-h2-q-20260719-9c271c1f/home/plugins/cache/mindthus-beta/mindthus-beta/2.0.0-next.3`
- plugin inventory: only `mindthus-beta@mindthus-beta`, enabled; see `plugin-list.json`
- Stable state: not installed in the isolated home
- packaged diagnostic: `integrity=ok`, `runtime_isolation_status=isolated-reported`; see `static-diagnostic.json`
- fixtures: all ten hashes verified; Q7 patches replay v0 -> v1 -> current
- case workspaces: no `AGENTS.md`
- repository verification: focused H2/H1/N3 `21/21`; full suite `642/642`
- H1 usage before H2: 9 Generator, 823,020 counted tokens
- H2 budget before Q1: 7 Generator calls and 3,176,980 total counted tokens remain
- frozen budget gate before Q1: `3,176,980 >= 200,000 * 7`

This proves candidate identity, package integrity, fixture identity, and reported runtime
isolation. It does not prove entry activation or semantic behavior. Q1 is the first live
call and freezes all candidate and case content.
