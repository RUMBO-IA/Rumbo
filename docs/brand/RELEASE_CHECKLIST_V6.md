# RUMBO Brand V6 release checklist

- [ ] canonical issue #72 is still open and authoritative
- [ ] canonical branch head equals expected parent
- [ ] candidate tree readback matches recorded SHA
- [ ] trusted Git identity satisfies active metadata rules
- [ ] one commit only; no force update
- [ ] canonical branch fast-forward readback exact
- [ ] brand workflow checks out exact PR head SHA
- [ ] actions/checkout and actions/setup-python remain SHA-pinned
- [ ] brand verifier compile PASS
- [ ] brand verifier current-surface PASS
- [ ] adversarial tests PASS
- [ ] privacy gate PASS
- [ ] commercial coherence PASS
- [ ] security headers PASS
- [ ] no unresolved review threads
- [ ] required reviews/status checks PASS
- [ ] publication authority separately proven
- [ ] production authority separately proven

Any unchecked required pre-publication item => SAFE_STOP.
