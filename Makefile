.PHONY: install release

install:
	@echo "Installing dependencies..."
	@poetry install
	@brew install gh

release:
	@echo "Bumping minor version"
	@poetry version minor
	@git add pyproject.toml
	@git commit -m "Bump version"
	@git push
	@git tag `poetry version -s --no-ansi`
	@git push --tags
	@gh release create `poetry version -s --no-ansi` --title `poetry version -s --no-ansi` --notes ""

test:
	@echo "Running tests..."
	@poetry run pytest 