# Security Policy

Report vulnerabilities to <https://github.com/neuron7x/FactSynth/security/advisories/new>.
Avoid public issues for sensitive findings.

## Secret scanning

GitHub's secret scanning and push protection are enabled to block commits that contain credentials or other tokens. Repository administrators should keep these protections active.

## Dependency review

Pull requests run a dependency review that fails when new dependencies contain known vulnerabilities of high severity. The main branch is protected and requires the "Dependency Review" check to pass before merging.
