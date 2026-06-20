from __future__ import annotations

from .entity_runtime import JsonObject, stable_hash, utc_now


def build_discovery_index(records: list[JsonObject]) -> JsonObject:
    indexed_records = []
    terms: dict[str, set[str]] = {}
    for record in records:
        record_id = record["entity_id"]
        indexed_records.append(record)
        for term in _record_terms(record):
            terms.setdefault(term, set()).add(record_id)
    index = {
        "schema_version": "1.0.0",
        "index_type": "stegtalk_discovery_index",
        "created_at": utc_now(),
        "record_count": len(indexed_records),
        "records": indexed_records,
        "terms": {term: sorted(ids) for term, ids in sorted(terms.items())},
    }
    index["index_hash"] = stable_hash(index)
    return index


def lookup_record(index: JsonObject, entity_id: str) -> JsonObject | None:
    for record in index.get("records", []):
        if record.get("entity_id") == entity_id:
            return record
    return None


def search_index(index: JsonObject, query: str) -> list[JsonObject]:
    query_terms = {term for term in _normalize(query).split() if term}
    if not query_terms:
        return []
    matching_ids: set[str] = set()
    for term in query_terms:
        matching_ids.update(index.get("terms", {}).get(term, []))
    return [record for record in index.get("records", []) if record.get("entity_id") in matching_ids]


def search_discovery(index: JsonObject, query: str, *, limit: int = 10) -> JsonObject:
    query_terms = {term for term in _normalize(query).split() if term}
    scored = []
    for record in index.get("records", []):
        record_terms = _record_terms(record)
        matched_terms = sorted(query_terms.intersection(record_terms))
        if matched_terms:
            scored.append(
                {
                    "entity_id": record["entity_id"],
                    "display_name": record["display_name"],
                    "score": len(matched_terms),
                    "matched_terms": matched_terms,
                    "record": record,
                }
            )
    scored.sort(key=lambda item: (-item["score"], item["display_name"].lower()))
    result = {
        "schema_version": "1.0.0",
        "result_type": "stegtalk_discovery_search_result",
        "query": query,
        "query_terms": sorted(query_terms),
        "result_count": min(len(scored), limit),
        "results": scored[:limit],
        "created_at": utc_now(),
    }
    result["result_hash"] = stable_hash(result)
    return result


def _record_terms(record: JsonObject) -> set[str]:
    parts = [
        record.get("entity_id", ""),
        record.get("display_name", ""),
        record.get("entity_type", ""),
        record.get("purpose", ""),
        " ".join(record.get("capabilities", [])),
        " ".join(record.get("boundaries", [])),
    ]
    return {term for term in _normalize(" ".join(parts)).split() if term}


def _normalize(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else " " for ch in value)
