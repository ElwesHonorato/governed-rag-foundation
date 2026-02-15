.PHONY: lineage-help lineage-namespaces lineage-jobs lineage-datasets lineage-search lineage-chunk

MARQUEZ_API_URL ?= http://localhost:5000/api/v1
LINEAGE_JOB_NAMESPACE ?= governed-rag
LINEAGE_DATASET_NAMESPACE ?= s3://rag-data
LINEAGE_PYTHONPATH := $(CURDIR)/libs/pipeline-common/src
q ?=
ns ?=

lineage-help:
	@echo "Lineage targets:"
	@echo "  make lineage-namespaces"
	@echo "  make lineage-jobs [ns=<namespace>]"
	@echo "  make lineage-datasets [ns=<namespace>]"
	@echo "  make lineage-search q=<text>"
	@echo "  make lineage-chunk q=<chunk_id>"
	@echo
	@echo "Environment overrides:"
	@echo "  MARQUEZ_API_URL=$(MARQUEZ_API_URL)"
	@echo "  LINEAGE_JOB_NAMESPACE=$(LINEAGE_JOB_NAMESPACE)"
	@echo "  LINEAGE_DATASET_NAMESPACE=$(LINEAGE_DATASET_NAMESPACE)"

lineage-namespaces:
	@MARQUEZ_API_URL="$(MARQUEZ_API_URL)" \
	LINEAGE_JOB_NAMESPACE="$(LINEAGE_JOB_NAMESPACE)" \
	LINEAGE_DATASET_NAMESPACE="$(LINEAGE_DATASET_NAMESPACE)" \
	PYTHONPATH="$(LINEAGE_PYTHONPATH)$(if $(PYTHONPATH),:$(PYTHONPATH),)" \
	python3 scripts/lineage/lineage.py namespaces

lineage-jobs:
	@MARQUEZ_API_URL="$(MARQUEZ_API_URL)" \
	LINEAGE_JOB_NAMESPACE="$(LINEAGE_JOB_NAMESPACE)" \
	LINEAGE_DATASET_NAMESPACE="$(LINEAGE_DATASET_NAMESPACE)" \
	PYTHONPATH="$(LINEAGE_PYTHONPATH)$(if $(PYTHONPATH),:$(PYTHONPATH),)" \
	python3 scripts/lineage/lineage.py jobs $(if $(strip $(ns)),$(ns),)

lineage-datasets:
	@MARQUEZ_API_URL="$(MARQUEZ_API_URL)" \
	LINEAGE_JOB_NAMESPACE="$(LINEAGE_JOB_NAMESPACE)" \
	LINEAGE_DATASET_NAMESPACE="$(LINEAGE_DATASET_NAMESPACE)" \
	PYTHONPATH="$(LINEAGE_PYTHONPATH)$(if $(PYTHONPATH),:$(PYTHONPATH),)" \
	python3 scripts/lineage/lineage.py datasets $(if $(strip $(ns)),$(ns),)

lineage-search:
	@if [ -z "$(strip $(q))" ]; then \
		echo "q is required. Example: make lineage-search q=<text>" >&2; \
		exit 1; \
	fi
	@MARQUEZ_API_URL="$(MARQUEZ_API_URL)" \
	LINEAGE_JOB_NAMESPACE="$(LINEAGE_JOB_NAMESPACE)" \
	LINEAGE_DATASET_NAMESPACE="$(LINEAGE_DATASET_NAMESPACE)" \
	PYTHONPATH="$(LINEAGE_PYTHONPATH)$(if $(PYTHONPATH),:$(PYTHONPATH),)" \
	python3 scripts/lineage/lineage.py search "$(q)"

lineage-chunk:
	@if [ -z "$(strip $(q))" ]; then \
		echo "q is required. Example: make lineage-chunk q=<chunk_id>" >&2; \
		exit 1; \
	fi
	@MARQUEZ_API_URL="$(MARQUEZ_API_URL)" \
	LINEAGE_JOB_NAMESPACE="$(LINEAGE_JOB_NAMESPACE)" \
	LINEAGE_DATASET_NAMESPACE="$(LINEAGE_DATASET_NAMESPACE)" \
	PYTHONPATH="$(LINEAGE_PYTHONPATH)$(if $(PYTHONPATH),:$(PYTHONPATH),)" \
	python3 scripts/lineage/lineage.py chunk "$(q)"
