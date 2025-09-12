**Incubation Pack merge note**: додано workflow `.github/workflows/release-artifact.yml`,
каталог `charts/factsynth`, `tests/test_openapi_contract.py`, `docs/INCUBATION_CO_DEV_UA.md`,
Makefile-таргети. Helm використовує `ghcr.io/neuron7x/factsynth` і
`.Chart.AppVersion` = версія з `pyproject.toml`.

### Rollback for branch cleanup

Якщо workflow з видаленням гілок видалив потрібну гілку, її можна відновити:

* `git fsck --no-reflogs` — пошук «висячих» комітів і створення гілки заново.
* Або відшукати гілку в локальних клонів/форків і запушити назад на віддалений репозиторій.
