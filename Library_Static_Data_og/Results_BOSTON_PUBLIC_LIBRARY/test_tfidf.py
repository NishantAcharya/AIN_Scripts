import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

def remove_most_repeated_words(docs, top_n=5):
    all_words = ' '.join(docs).split()
    word_counts = Counter(all_words)
    most_common = set([w for w, _ in word_counts.most_common(top_n)])
    cleaned_docs = []
    for doc in docs:
        cleaned = ' '.join([w for w in doc.split() if w not in most_common])
        cleaned_docs.append(cleaned)
    return cleaned_docs

def compare_lines_tfidf(lines, top_n=5):
    cleaned_lines = remove_most_repeated_words(lines, top_n=top_n)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(cleaned_lines)
    similarity = (tfidf_matrix * tfidf_matrix.T).toarray()
    return similarity

def filter_similar_lines(lines, similarity_matrix, threshold=0.7):
    n = len(lines)
    keep = [True] * n
    for i in range(n):
        if not keep[i]:
            continue
        for j in range(i+1, n):
            if similarity_matrix[i, j] > threshold:
                keep[j] = False
    filtered_lines = [line for line, k in zip(lines, keep) if k]
    return filtered_lines

if __name__ == "__main__":
    with open('Library_Static_Data_og/Results_BOSTON_PUBLIC_LIBRARY/provider_set.txt', 'r') as file:
        lines = [line.strip() for line in file if line.strip()]


    sim_matrix = compare_lines_tfidf(lines, top_n=3)
    print("Cosine similarity matrix (excluding most repeated words):")
    print(np.round(sim_matrix, 2))

    filtered_lines = filter_similar_lines(lines, sim_matrix, threshold=0.7)
    print("\nFiltered lines (duplicates removed):")
    print(len(lines), len(filtered_lines))