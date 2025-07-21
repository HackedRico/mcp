
def search_cti_title(query: str) -> list[str]:
    """Returns top-5 results and then the names of the top-5 to top-30 results."""

    topK = search(query, 30)
    names, topK = [f"`{x.split(' | ')[0]}`" for x in topK[5:30]], topK[:5]
    return topK + [f"Other retrieved pages have names: {', '.join(names)}."]

def search_cti_data_by_title(name: str) -> str:
    """Returns the full CTI data for a given name."""
    if name in adv_step:
        return adv_step[name]

    results = [x for x in search(name, 10) if x.startswith(name + " | ")]
    if not results:
        return f"No CTI data found for name: {name}"
    return results[0]

def extract_text_chunks(stix_bundle):
    text_chunks = []
    adv_step = {}
    for obj in stix_bundle.get("objects", []):
        if obj.get("type") in [
            "attack-pattern", "malware", "tool", "threat-actor", "intrusion-set", "identity", "indicator", "report"
        ]:
            name = obj.get("name", "")
            description = obj.get("description", "")

            if name or description:
                adv_step[name] = description
                text_chunks.append(f"{name} | {description}")
    return text_chunks, adv_step

max_characters = 6000 
topk_objects_to_retrieve = 5
corpus, adv_step = extract_text_chunks(stix_bundle)
embedder = dspy.Embedder('openai/text-embedding-3-small', dimensions=512)
search = dspy.retrievers.Embeddings(embedder=embedder, corpus=corpus, k=topk_objects_to_retrieve)