import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import re
import cohere
from openai import OpenAI
from swag import tools
from swag.prompts import ToolRetriever

tr = tools.ToolRegistry()
co = cohere.ClientV2(api_key="E6Co5OUVwzw0l0UfHYZoZ2JBUvbPkc1qseEdN0Rr") # type: ignore
client = OpenAI()

docs = [f"{tool}, {tr.get(tool)[1].model_json_schema()['description']}" for tool in tr.tools]
queries = [
    "How do I get from Paris to Marseille?",
    "What is this statue?",
    "Tell me more about the architecture of this building.",
    "Take me on a scenic route to the beach."
]

expected_tools = [
    ["OptimizeRoute", "GetDirections", "GetDistanceMatrix", "Geocode", "GetNearestRoads"],
    ["SearchInternet", "ReadWebsite", "SearchGoogleMapsWithText", "GetDetailsOfPlace", "GetPhoto"],
    ["SearchInternet", "ReadWebsite", "SearchGoogleMapsWithText", "GetDetailsOfPlace", "GetPhoto", "SearchForNearbyPlacesOfType"],
    ["OptimizeRoute", "GetDirections", "GetDistanceMatrix", "Geocode", "GetNearestRoads"]
]


rerank_tools = []

for q in queries:
    query_tools = []
    response = co.rerank(
            model="rerank-v3.5",
            query=q,
            documents=docs,
            top_n=10
    )
    for i, r in enumerate(response.results):
        query_tools.append(docs[r.index].split(",")[0])

    rerank_tools.append(query_tools)

haiku_tools = []

for q in queries:
    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": str(ToolRetriever(tools=docs))}, {"role": "user", "content": q}]
    )

    pattern = re.compile(r"<relevant_tools>(.*)</relevant_tools>", re.DOTALL)
    text = response.choices[0].message.content
    if not text:
        continue
    match = pattern.search(text)
    if match:
        extracted_tools = [t.strip() for t in match.group(1).split(",")]
        haiku_tools.append(extracted_tools)

total_acc = 0
total_prec = 0
total_rec = 0

for i, (rt, ht) in enumerate(zip(rerank_tools, haiku_tools)):
    print(f"Query: {queries[i]}")
    rrf = {}
    k = 60

    for j, tool in enumerate(rt):
        rrf[tool] = rrf.get(tool, 0) + (1 / (k + j + 1))

    for j, tool in enumerate(ht):
        rrf[tool] = rrf.get(tool, 0) + (1 / (k + j + 1))

    rff = sorted(rrf.items(), key=lambda x: x[1], reverse=True)
    print(rff)
    print("="*50)
    rrf_tools = [r[0] for r in rff[:6]]

    tp = 0

    fp = 0

    for et in expected_tools[i]:
        if et in rrf_tools:
            tp += 1

    fp = len(rrf_tools) - tp
    fn = len(expected_tools[i]) - tp
    tn = len(docs) - (tp + fp + fn)

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    acc = (tp + tn) / (tp + fp + fn + tn)
    print(f"Expected tools: {expected_tools[i]}")
    print(f"Predicted tools: {rrf_tools}")
    print(f"Accuracy: {acc}")
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print("="*50)


    total_acc += acc
    total_prec += precision
    total_rec += recall

print(f"Mean accuracy: {total_acc / len(queries)}")
print(f"Mean precision: {total_prec / len(queries)}")
print(f"Mean recall: {total_rec / len(queries)}")


