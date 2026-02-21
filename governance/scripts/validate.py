#!/usr/bin/env python3
"""Validate governance YAML integrity and cross-reference consistency."""

from __future__ import annotations

from collections import Counter

from _common import ID_PATTERN, load_model


def _matches_rule(dataset: dict, rule: dict) -> bool:
    """Return true when a mapping rule applies to a dataset definition."""

    match = rule.get("match", {})
    platform_ok = match.get("dataset_platform") == dataset.get("platform")
    prefix = match.get("dataset_name_prefix")
    prefix_ok = isinstance(prefix, str) and str(dataset.get("name", "")).startswith(prefix)
    return platform_ok and prefix_ok


def main() -> int:
    """Run validation checks and return a shell-compatible status code."""

    model = load_model()
    errors: list[str] = []

    domains = {d["id"] for d in model.domains}
    groups = {g["id"] for g in model.groups}
    tags = {t["id"] for t in model.tags}
    terms = {t["id"] for t in model.terms}

    # All IDs unique + naming convention.
    all_ids: list[str] = []
    for section in [model.domains, model.groups, model.tags, model.terms, model.datasets]:
        for item in section:
            item_id = str(item.get("id", ""))
            if not item_id:
                errors.append(f"missing id in item: {item}")
                continue
            all_ids.append(item_id)
            if not ID_PATTERN.match(item_id):
                errors.append(f"invalid id format: {item_id}")

    dupes = [item_id for item_id, count in Counter(all_ids).items() if count > 1]
    for dup in dupes:
        errors.append(f"duplicate id: {dup}")

    # Domain parent references.
    for domain in model.domains:
        parent = domain.get("parent")
        if parent and parent not in domains:
            errors.append(f"domain '{domain['id']}' references unknown parent '{parent}'")

    dataset_ids = {d["id"] for d in model.datasets}

    for dataset in model.datasets:
        if not dataset.get("domain"):
            errors.append(f"dataset '{dataset['id']}' missing domain")
        if not dataset.get("owners"):
            errors.append(f"dataset '{dataset['id']}' missing owners")

        if dataset.get("domain") and dataset["domain"] not in domains:
            errors.append(f"dataset '{dataset['id']}' references unknown domain '{dataset['domain']}'")

        for owner in dataset.get("owners", []):
            if owner not in groups:
                errors.append(f"dataset '{dataset['id']}' references unknown owner group '{owner}'")
        for tag in dataset.get("tags", []):
            if tag not in tags:
                errors.append(f"dataset '{dataset['id']}' references unknown tag '{tag}'")
        for term in dataset.get("terms", []):
            if term not in terms:
                errors.append(f"dataset '{dataset['id']}' references unknown glossary term '{term}'")

    for pipeline in model.pipelines:
        flow = pipeline.get("flow", {})
        flow_id = flow.get("id", "<missing>")

        if flow.get("domain") not in domains:
            errors.append(f"flow '{flow_id}' references unknown domain '{flow.get('domain')}'")
        if not flow.get("owners"):
            errors.append(f"flow '{flow_id}' missing owners")
        for owner in flow.get("owners", []):
            if owner not in groups:
                errors.append(f"flow '{flow_id}' references unknown owner group '{owner}'")

        job_ids = {job["id"] for job in pipeline.get("jobs", [])}
        for job in pipeline.get("jobs", []):
            if not job.get("domain"):
                errors.append(f"job '{job['id']}' missing domain")
            if not job.get("owners"):
                errors.append(f"job '{job['id']}' missing owners")
            if job.get("domain") and job["domain"] not in domains:
                errors.append(f"job '{job['id']}' references unknown domain '{job['domain']}'")
            for owner in job.get("owners", []):
                if owner not in groups:
                    errors.append(f"job '{job['id']}' references unknown owner group '{owner}'")

        for contract in pipeline.get("lineage_contract", []):
            if contract.get("job") not in job_ids:
                errors.append(f"lineage contract references unknown job '{contract.get('job')}'")
            for ds in contract.get("inputs", []) + contract.get("outputs", []):
                if ds not in dataset_ids:
                    errors.append(f"lineage contract references unknown dataset '{ds}'")

    # Rule coverage for S3 datasets.
    s3_datasets = [d for d in model.datasets if d.get("platform") == "s3"]
    for dataset in s3_datasets:
        if not any(_matches_rule(dataset, rule) for rule in model.mapping_rules):
            errors.append(
                f"mapping rule coverage missing for s3 dataset '{dataset['id']}' ({dataset['name']})"
            )

    if errors:
        print("Validation failed:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("Validation passed.")
    print(f"- domains: {len(model.domains)}")
    print(f"- groups: {len(model.groups)}")
    print(f"- tags: {len(model.tags)}")
    print(f"- terms: {len(model.terms)}")
    print(f"- datasets: {len(model.datasets)}")
    print(f"- pipelines: {len(model.pipelines)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
