import os
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from collections import Counter
import json

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

with open(input_file, 'r') as f:
    lines = f.readlines()
    val_libs = ['Results_' + line.strip().split('~')[2].strip().replace(' ', '_') for line in lines]

for folder in val_libs:
    folder_path = os.path.join(directory, folder)
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist, skipping...")
        continue
    
    files = [file for file in os.listdir(folder_path)]
    if 'provider_set.txt' not in files:
        print(f"File provider_set.txt not found in {folder_path}, skipping...")
        continue

    with open(os.path.join(folder_path, 'provider_set.txt'), 'r') as f:
        providers = [line.strip() for line in f if line.strip()]
    if not providers:
        print(f"No providers found in {folder_path}, skipping...")
        continue

    documents.extend(providers)

with open('all_providers.txt', 'w') as f:
        for provider in documents:
            f.write(provider + '\n')

#Pre process documents
documents = [doc.lower() for doc in documents]  # Convert to lowercase
documents = [doc.replace(',', '') for doc in documents]  # Remove commas
documents = [doc.replace('.', '') for doc in documents]  # Remove periods
documents = [doc.replace('-', ' ') for doc in documents]  # Remove hyphens
documents = [doc.replace('&', '') for doc in documents]  # Remove ampersands

#Finding the top 3 words per line in the document
vectorizer = TfidfVectorizer(
    stop_words=common_english_filler_words + telecom_company_name_common_words,
    lowercase=True,
    token_pattern=r'\b[a-zA-Z][a-zA-Z]+\b'
)
tfidf_matrix = vectorizer.fit_transform(documents)
feature_names = np.array(vectorizer.get_feature_names_out())

top_words = []
for row in tfidf_matrix:
    row_data = row.toarray().flatten()
    if np.count_nonzero(row_data) == 0:
        continue
    top_indices = row_data.argsort()[-3:][::-1]
    words = feature_names[top_indices]
    top_words.extend([w for w in words if row_data[feature_names.tolist().index(w)] > 0])


word_freq = Counter(top_words)
with open('top_words_frequency.json', 'w') as f:
    json.dump(word_freq, f, indent=2)