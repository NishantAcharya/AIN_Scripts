from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

input_file = 'validation_input.txt'
directory = './Library_Static_Data/'

# Sample documents
documents = [
]
common_english_filler_words = ['the', 'and', 'a', 'to', 'of', 'in', 'is', 'that', 'it', 'for', 'on', 'with', 'as', 'this', 'by', 'at']
telecom_company_name_common_words = [
    "ltd",
    "llc",
    "inc",
    "co",
    "corporation",
    "company",
    "communications",
    "telecom",
    "solutions",
    "systems",
    "networks",
    "global",
    "international",
    "wireless",
    "mobile",
    "broadband",
    "data",
    "tech",
    "technology",
    "group",
    "ventures",
    "holdings",
    "enterprises",
    "alliance",
    "connect",
    "digital",
    "tel",
    "optic",
    "fiber",
    "cooperative",
    "association",
    "services",
    "corp",
    "limited",
    "plc",
    "ag",
    "gmbh",
    "sa",
    "nv",
    "pt",
    "sarl",
    "srl",
    "ab",
    "college",
    "school",
    "university",
    "high",
    "academy",
    "institute",
    "community",
    "state",
    "technology",
    "tech",
    "telephone",
    "district",
    "middle",
    "k12",
    "oy"
]

def get_top_words_and_filter_duplicates(original_lines):
    inputs = original_lines.copy()
    inputs = [doc.lower() for doc in inputs]  # Convert to lowercase
    inputs = [doc.replace(',', '') for doc in inputs]  # Remove commas
    inputs = [doc.replace('.', '') for doc in inputs]  # Remove periods
    inputs = [doc.replace('-', ' ') for doc in inputs]  # Remove hyphens
    inputs = [doc.replace('&', '') for doc in inputs]  # Remove ampersands
    # Remove any word from common English filler words and telecom company name common words
    inputs = [
        ' '.join([
            word for word in doc.split()
            if word not in common_english_filler_words and word not in telecom_company_name_common_words
        ])
        for doc in inputs
    ]

    vectorizer = TfidfVectorizer()
    vectorizer.fit(inputs)
    tfidf_matrix = vectorizer.transform(inputs)
    vocabulary = vectorizer.vocabulary_
    tfidf_scores = tfidf_matrix.toarray()

    seen_top_word_sets = []
    filtered_lines = []
    for i, document in enumerate(tfidf_scores):
        # Get the actual words in the processed line
        words_in_line = [w for w in inputs[i].split() if w.strip()]
        num_words = min(3, len(words_in_line)) if len(words_in_line) > 0 else 0
        if np.count_nonzero(document) == 0:
            top_words = words_in_line[:num_words]
        else:
            sorted_indices = np.argsort(document)[::-1]
            top_words = []
            for index in sorted_indices:
                word = list(vocabulary.keys())[list(vocabulary.values()).index(index)]
                if word in words_in_line and word not in top_words:
                    top_words.append(word)
                if len(top_words) == num_words:
                    break
        top_words_set = set(top_words)
        has_intersection = any(len(top_words_set & prev_set) > 0 for prev_set in seen_top_word_sets)
        if not has_intersection:
            seen_top_word_sets.append(top_words_set)
            filtered_lines.append(original_lines[i])
    return filtered_lines

# Example usage:
filtered_documents = get_top_words_and_filter_duplicates(documents)

print(len(filtered_documents),len(documents))
#Compare the original and filtered lists for which words are removed
removed_words = set(documents) - set(filtered_documents)
print("Removed words:")
for word in removed_words:
    print(word)