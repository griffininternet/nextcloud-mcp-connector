# Deferred items of phase 13

Findings that are out of scope for the plan that found them. Nothing here was fixed.

| Found in | Item | Why deferred |
|----------|------|--------------|
| 13-05, run `32883904698` | The release workflow carries the annotation "Node.js 20 is deprecated" for five actions: `docker/build-push-action@v6`, `docker/login-action@v3`, `docker/setup-buildx-action@v3`, `docker/setup-qemu-action@v3` and `softprops/action-gh-release@v2`. GitHub already forces them onto Node.js 24, so the run is green and the release is unaffected | Pre-existing: the same annotation was on the 0.1.8 run, and none of the five actions is touched by this phase. Raising the action majors is a change to `.github/workflows/release.yml`, which this plan only executes. It belongs to a maintenance plan, together with the reminder the deprecation rule asks for (issue plus a dated reminder), and it must not be bundled into the release that is being published. RESOLVED 2026-08-26 after the release: all actions raised to their node24 majors in both workflows (commit 64fb200, setup-uv pinned to v10.0.1 in the follow-up because it stopped publishing floating major tags); validated by a green CI run 32923833778 and a green release dry run 32923698977, both without the deprecation annotation. No issue or reminder needed anymore |
