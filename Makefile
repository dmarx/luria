# Job bodies live here, not in the workflow YAML, so "run what CI runs" is
# always `make <target>` and the two can't drift apart.

.PHONY: help ci install test lint link index journal ref-status pending reports collect

help:
	@grep -E '^[a-z][a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

install: ## editable install with dev extras
	pip install -e ".[dev]"

ci: test lint ## everything CI runs

test: ## the unit suite
	python -m pytest tests -q

lint: ## the docs lint — the only target that fails on the record
	luria lint

link: ## rewrite bare references as hyperlinks
	luria link --fix

index: ## regenerate the decision index from frontmatter
	luria index

journal: ## what the devlog has filed, and which books it renders to
	luria journal

ref-status: ## references to retired documents, every site
	luria ref-status --all

pending: ## undecided decisions by age and citation count
	luria pending

reports: ## write both reports to build/doc-reports/
	luria reports

remotes: ## other projects' records: how each foreign reference resolves
	luria remotes

remotes-refresh: ## rediscover remote filenames into remotes.lock.json
	luria remotes --refresh

collect: ## assemble fragment directories into their views
	luria collect
