## Summary

-

## Verification

- [ ] `python3 tools/verify_release.py`
- [ ] `python3 tools/verify_release.py --source-check required` for release or coverage-matrix changes
- [ ] Documentation updated, if user-facing behavior changed

## Boundary Check

- [ ] This preserves the "workflow adaptation, not model replacement" boundary.
- [ ] This does not add credentials, private prompt text, or hidden provider assumptions.
- [ ] Current product/provider/API claims are backed by official sources when applicable.
