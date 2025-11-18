# Deployment — Packaging as a Python Framework

Goal: this repository is intended to be distributed as a Python framework / package. The deployment flow is to review and update `setup.py`, build distributions (wheel + sdist), test locally, then push the repository (and a release tag) to GitHub or GitLab. Optionally, publish the package to PyPI or a registry (GitLab Package Registry).

Checklist (high-level)

- [ ] Review and update metadata in `setup.py` (name, version, description, author, url, license, install_requires, python_requires, packages).
- [ ] Sync `requirements.txt` with `install_requires` in `setup.py` if needed.
- [ ] Use `README.md` as the `long_description` in `setup.py` for rich package pages.
- [ ] Bump the package version (follow SemVer) and commit the change.
- [ ] Build distributions (wheel and sdist) and test them locally.
- [ ] Create a git tag (e.g. `v1.2.0`) and push it to the remote.
- [ ] Push the repository to GitHub or GitLab (including tags).
- [ ] (Optional) Publish to PyPI or GitLab Package Registry using CI/CD or `twine`.

Detailed steps

1) Inspect and update `setup.py`

Open `setup.py` and make sure the key fields are set appropriately:

- `name`: a unique package name (on PyPI) or the installable name when using `pip install git+...`.
- `version`: follow PEP 440 (e.g. `0.3.1` or `1.0.0`).
- `description` and `long_description` (read long description from `README.md`).
- `author`, `author_email`, `url` (link to the GitHub/GitLab project).
- `packages` or `packages=find_packages()` to include the project modules.
- `install_requires`: list runtime dependencies (can be synced with `requirements.txt`).
- `python_requires`: e.g. `>=3.10`.
- `classifiers`: include appropriate classifiers (License, Programming Language, etc.).
- `include_package_data=True` and `package_data` if you bundle non-Python files.

Minimal example (adapt to the project):

```python
# setup.py (minimal example)
from setuptools import setup, find_packages
from pathlib import Path

README = Path("README.md").read_text()

setup(
    name="vetc_tool_function",  # change to your desired package name
    version="0.1.0",
    description="Small helper tools for data connectors",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="you@example.com",
    url="https://gitlab.com/yourorg/yourrepo",
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        # example - keep in sync with requirements.txt
        "pandas>=1.5",
        "google-api-python-client>=2.0",
    ],
    python_requires=">=3.10",
    include_package_data=True,
)
```

2) Synchronize dependencies

- If you maintain a `requirements.txt`, make sure `install_requires` lists the runtime dependencies needed by users of the package.
- Exclude development-only tools (linters, test frameworks) from `install_requires`.

3) Bump version, commit, and tag

- Update the `version` in `setup.py`.
- Commit the changes and create an annotated tag:

```bash
git add setup.py README.md
git commit -m "chore(release): prepare release v1.2.0"
git tag -a v1.2.0 -m "Release v1.2.0"
```

4) Build the package locally

Install the build tool and create distributions:

```bash
python -m pip install --upgrade build
python -m build
```

This produces files under the `dist/` directory (`.whl` and `.tar.gz`).

5) Test installation locally

Install the generated wheel to verify packaging and import paths:

```bash
python -m pip install dist/your_package_name-0.1.0-py3-none-any.whl
```

Or install directly from a Git tag to simulate user install before publishing:

```bash
pip install git+https://github.com/yourorg/yourrepo.git@v1.2.0
# or GitLab
pip install git+https://gitlab.com/yourgroup/yourrepo.git@v1.2.0
```

6) Push the repository and tags to remote

If the repository has no remote configured, add one and push:

```bash
git remote add origin git@github.com:yourorg/yourrepo.git
git push -u origin main
# push tags
git push origin --tags
```

7) (Optional) Publish to PyPI

- Create a PyPI account if you don't have one. Use TestPyPI first to verify the publishing process.
- Install `twine` and upload the distributions:

```bash
python -m pip install --upgrade twine
python -m twine upload dist/*
# For TestPyPI
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

Security note: use API tokens and avoid putting credentials in the repository. Store tokens as CI secrets or environment variables.

8) (Optional) Automate publishing in CI (GitLab CI / GitHub Actions)

- Configure a CI job that builds and publishes when a tag matching `v*` is pushed.
- Store registry/PyPI tokens as protected CI variables.

Example GitLab CI job triggered by tags:

```yaml
stages:
  - release

release:
  image: python:3.10-slim
  stage: release
  script:
    - python -m pip install --upgrade build twine
    - python -m build
    - python -m twine upload -u __token__ -p "$PYPI_TOKEN" dist/*
  only:
    - tags
```

For GitHub Actions, create a workflow triggered on `push` to tags like `v*` and use the `PYPI_API_TOKEN` secret.

9) Update changelog and release notes

- Before publishing, update `CHANGELOG.md` or prepare release notes describing the changes in this release.
- Create a Release entry in GitHub/GitLab from the annotated tag and add the release notes.

10) Post-release verification

- Install the package from PyPI (if published) into a clean environment to validate the release:

```bash
pip install vetc_tool_function==1.2.0
python -c "import vetc_tool_function; print(vetc_tool_function.__version__)"
```

- Verify public APIs (functions under `tools/`) import and behave as expected.

Best practices & recommendations

- Follow Semantic Versioning (MAJOR.MINOR.PATCH).
- Keep `README.md` clear; use it as the `long_description` for package pages.
- Never commit secrets (service-account JSON, tokens). Use CI variables or a secrets manager.
- Automate release publishing via CI: push tag -> CI builds & publishes.
- Run unit and integration tests before creating a release tag.

Quick install-from-Git example

```bash
pip install git+https://github.com/yourorg/yourrepo.git@v1.2.0
```

Conclusion

This repository should be packaged by completing `setup.py` metadata, building and testing locally, then pushing the repo and a release tag to GitHub or GitLab. Optionally publish built distributions to PyPI or a private registry for easy consumption by other projects.
