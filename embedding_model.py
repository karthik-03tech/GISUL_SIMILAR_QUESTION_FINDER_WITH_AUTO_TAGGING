from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")  # ~80MB, downloads once

TOPICS = {
    "Biology":          ["photosynthesis", "cell", "DNA", "evolution", "respiration", "protein", "organism"],
    "Physics":          ["force", "gravity", "energy", "motion", "light", "wave", "electron", "velocity"],
    "Chemistry":        ["reaction", "molecule", "element", "acid", "bond", "compound", "atom"],
    "Mathematics":      ["equation", "integral", "derivative", "geometry", "probability", "function"],
    "History":          ["war", "civilization", "empire", "revolution", "century", "government", "treaty"],
    "Computer Science": ["algorithm", "data structure", "network", "program", "database", "recursion"],
    "General":          []
}

topic_sentences = {
    topic: " ".join(keywords)
    for topic, keywords in TOPICS.items() if keywords
}

# Pre-compute topic embeddings once at startup
topic_embeddings = {
    topic: model.encode(sentence)
    for topic, sentence in topic_sentences.items()
}


def get_embedding(text: str) -> list:
    """Return embedding as a plain Python list (JSON-serialisable)."""
    return model.encode(text).tolist()


def assign_tag(question: str) -> str:
    """Classify a question into the closest TOPICS category."""
    q_embedding = model.encode(question)
    best_topic = "General"
    best_score = 0.0
    for topic, t_emb in topic_embeddings.items():
        score = cosine_similarity([q_embedding], [t_emb])[0][0]
        if score > best_score:
            best_score = score
            best_topic = topic
    return best_topic


def find_similar(new_embedding: list, all_questions: list, top_n: int = 5) -> list:
    """
    Given a new embedding and a list of dicts with keys
    'embedding', 'text', 'tag', return up to top_n similar entries
    sorted by cosine similarity (score > 0.3 only).
    """
    if not all_questions:
        return []

    stored = [(q, q["embedding"]) for q in all_questions if "embedding" in q]
    if not stored:
        return []

    embeddings_matrix = np.array([e for _, e in stored])
    scores = cosine_similarity([new_embedding], embeddings_matrix)[0]

    ranked = sorted(zip(scores, [q for q, _ in stored]), reverse=True)
    return [
        {"text": q["text"], "tag": q["tag"], "score": round(float(s), 3)}
        for s, q in ranked[:top_n]
        if s > 0.3   # only show meaningfully similar results
    ]
