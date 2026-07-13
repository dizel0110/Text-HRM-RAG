import urllib.request
import os

papers = [
    ("A-RAG", "2602.03442", "A-RAG_Scaling_Agentic_Retrieval-Augmented_Generation_via_Hierarchical_Retrieval_Interfaces"),
    ("RAG", "2005.11401", "Retrieval-Augmented_Generation_for_Knowledge-Intensive_NLP_Tasks"),
    ("ReAct", "2210.03629", "ReAct_Synergizing_Reasoning_and_Acting_in_Language_Models"),
    ("Self-Ask", "2210.03350", "Measuring_and_Narrowing_the_Compositionality_Gap_in_Language_Models"),
    ("CoT", "2201.11903", "Chain-of-Thought_Prompting_Elicits_Reasoning_in_Large_Language_Models"),
    ("RAPTOR", "2401.18059", "RAPTOR_Recursive_Abstractive_Processing_for_Tree-Organized_Retrieval"),
    ("HotpotQA", "1809.09600", "HotpotQA_A_Dataset_for_Diverse_Explainable_Multi-hop_Question_Answering"),
    ("GRASP", "2605.16598", "GRASP_Graph_Agentic_Search_over_Propositions_for_Multi-hop_Question_Answering"),
    ("HERA", "2604.00901", "HERA_Experience_as_a_Compass_Multi-agent_RAG_with_Evolving_Orchestration"),
]

out_dir = os.path.join(os.path.dirname(__file__), "..", "papers")
os.makedirs(out_dir, exist_ok=True)

for short, arxiv_id, filename in papers:
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    path = os.path.join(out_dir, f"{filename}.pdf")
    if os.path.exists(path):
        print(f"  EXISTS  {short} — {filename}.pdf")
        continue
    try:
        print(f"  DOWNLOAD {short} — {url}")
        urllib.request.urlretrieve(url, path)
        print(f"  OK      {short} ({os.path.getsize(path) // 1024} KB)")
    except Exception as e:
        print(f"  FAIL    {short}: {e}")

print("Done.")
