# Whispera-K v0.2.18 — RUMBO hardening experiment

This directory defines a reproducible hardening overlay for the public upstream
`kazu00001/Whispera-K` at exactly:

- Tag: `v0.2.18`
- Commit: `3bbd712e0391287a01d264af6bcac43023965ac6`

It does **not** modify the upstream repository and it is **not** a production
release.

## Remediations applied

- Require Tauri core >= 2.11.6 and Tauri CLI 2.12.0.
- Pin updater crate 2.12.0.
- Enable updater `requireSignedVersion`.
- Explicitly disable downgrade acceptance.
- Replace the ffmpeg-static lifecycle download with a pinned, SHA-256 verified
  FFmpeg 9.0.2 Windows LGPL build.
- Default global clipboard capture to OFF.
- Default automatic video transcription and transcript attachment to OFF.
- Default incremental transcription to OFF.
- Restore dictionary compare-and-swap and previous-revision retention from the
  canonical upstream behavior.
- Restrict arbitrary audio-file transcription to the native import window.
- Disable periodic background updater polling; updates are manual in this
  profile.
- Bound updater SQLite backups to at most three.
- Add vulnerability gates, native tests, UI regression tests, and an unsigned
  verification build.

## Verification contract

The workflow first runs the hardening verifier against pristine v0.2.18 and
requires an expected RED. It then applies the overlay and requires GREEN before
security audits and full tests.

A successful workflow artifact contains:

- the generated unified patch;
- updated `Cargo.lock`;
- updated `package-lock.json`;
- the hardening provenance marker;
- receipts containing source, FFmpeg, and installer hashes;
- an **unsigned verification installer**.

The installer is for CI verification only. Distribution remains NO_GO until a
separate signed release process provides version-bound updater signatures,
Windows code signing where required, immutable release provenance, and a
reviewed promotion decision.
