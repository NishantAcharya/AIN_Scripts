import re
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import os
from pathlib import Path

filtered_words = ["fiber", "parent"]
abbre_name = ["Utah Telecommunication Open Infrastructure Agency"]
abbre_set = ["utopia"]
#This py file is used to extract important words for FCC provider
#provider_path = "providers.json"

#file_name1 = parent_dir  / ".." / "Data_set" / "bulk_whois" / "Organizations.txt"
#file_name2 = parent_dir  / ".." / "Data_set" / "FCC_providers" / "BDC.xlsx"

#input files
parent_dir = Path(__file__).resolve().parent
name_path = Path(__file__).resolve().parent / "nameset.txt"
idf_path = Path(__file__).resolve().parent / "idf.txt"
tf_idf_path = Path(__file__).resolve().parent/ "tf_idf.txt"
provdier_names = Path(__file__).resolve().parent / ".." / "FCC_Provider" / "FCC_providers.txt"
keywords_file = Path(__file__).resolve().parent/ "provider_keywords.txt"
keyword_for_every_name = Path(__file__).resolve().parent / ".." / "outputs" / "FCC_providers.txt"
provider_no_keyword_path = Path(__file__).resolve().parent / ".." / "outputs" / "provider_no_keyword.txt"

#This set is manually generated, to make it up-to-date, use extract_special.py to see whether other special chars remains
remain_char = [chr(38), chr(95), chr(45), chr(42), chr(46), chr(39), chr(96), chr(64), chr(63),chr(43), chr(61), chr(35), chr(58), chr(94), chr(62),  chr(37) , chr(126), chr(92), chr(124), chr(33)]
#remain_char = []
keyword_set = []

class Provider:
    def __init__(self, brand, provider_name, holding_company):
        self.brand = clean_string(brand)
        self.provider_name = clean_string(provider_name)
        self.holding_company = clean_string(holding_company)
        self.keywords = []
    def add_keyword(self, word):
        self.keywords.append(word)
    def add_potential_words(self, word):
        self.potential_words.append(word)
    def get_brand(self):
        return self.brand
    def get_provider_name(self):
        return self.provider_name
    def get_holding_company(self):
        return self.holding_company
    def get_keywords(self):
        return self.keywords

def clean_string(text):
    return " ".join(word.replace(".", "") for word in text.split())      


def check_abbreviation(name):
    if name not in abbre_name:
        return "0"
    else:
        ind = abbre_name.index(name)
        return abbre_set[ind]

provider_set = []
provider_name_set = []
with open(provdier_names, "r") as file:
    input_json = json.load(file) 
    for providers in input_json:
        p = Provider(providers["brand"], providers["provider_name"], providers["holding_company"])
        provider_set.append(p)
        provider_name_set.append(clean_string(providers["brand"]))
        provider_name_set.append(clean_string(providers["holding_company"]))
        provider_name_set.append(clean_string(providers["provider_name"]))


#Get name set
name_set = []
name_set.extend(provider_name_set)
with open(name_path, "r") as file:
    for line in file:
        name = line.strip()
        name = re.sub(r'\.+', '.', name)
        name_set.append(name)
name_set = list(set(name_set))
#for item in name_set:
    #print(item)
#print(f"The size of name set is {str(len(name_set))}")

#divide provider names into words
provider_words = [word for s in provider_name_set for word in s.split()]

#---------------------------------------------------
#TF-IDF
# create object
special_chars_regex = re.escape("".join(remain_char))
token_pattern = rf"(?u)[\w{special_chars_regex}]+"
tfidf = TfidfVectorizer(token_pattern=token_pattern)


# get tf-df values
result = tfidf.fit_transform(name_set)

num_documents = result.shape[0] 
print(f"The Corpus contains {str(num_documents)} number of strings")
#print("======================================================")

if not os.path.exists(idf_path):
    with open(idf_path, "w") as file:
        feature_idf_pairs = zip(tfidf.get_feature_names_out(), tfidf.idf_)
        sorted_pairs = sorted(feature_idf_pairs, key=lambda x: x[1], reverse=True)
        for ele1, ele2 in sorted_pairs:
            if ele2 <= 8:
                file.write(f"{ele1}: {ele2}\n")
'''
#show tf-idf value for each words in provider names
with open(tf_idf_path, "w") as file:
    feature_names = tfidf.get_feature_names_out()
    a_tfidf = tfidf.transform(provider_name_set)
    for i, text in enumerate(provider_name_set):
        row = a_tfidf[i]
        indices = row.indices
        values = row.data
        word_tfidf = {feature_names[idx]: val for idx, val in zip(indices, values)}
        sorted_tfidf = sorted(word_tfidf.items(), key=lambda x: x[1], reverse=True)
        if sorted_tfidf:
            file.write(f"TF-IDF values for '{provider_name_set[i]}':\n")
            for word, score in sorted_tfidf:
                file.write(f"{word}: {score:.4f}-----------------{tfidf.idf_[tfidf.vocabulary_[word]]}\n")
        else:
            file.write("No relevant words found in TF-IDF model.\n")
        #file.write("---------------------------------------------\n")
 '''
with open(keyword_for_every_name, "w") as key_word_file:
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    for p in provider_set:
        jjj = 0
        #check brand name
        i = 0
        abb = check_abbreviation(p.get_brand())
        if abb == "0":
            string_index = name_set.index(p.get_brand())   
            target_tfidf_values = result[string_index].toarray()[0]
            feature_names = tfidf.get_feature_names_out()
            for word, value in zip(feature_names, target_tfidf_values):
                if value >= 0.7:  
                    i = 1
                    if word not in filtered_words:
                        p.add_keyword(word)
                        jjj = 1
                        key_word_file.write("brand name: " + p.get_brand() + " keyword: " + word + " and tf-idf value: " + str(value) + "\n")
            if i == 0:
                w = ""
                v = 0
                for word, value in zip(feature_names, target_tfidf_values):
                    if value > v:  
                        v = value
                        w = word
                if w not in filtered_words:
                    p.add_keyword(w)
                    jjj = 1
                    key_word_file.write("brand name: " + p.get_brand() + " keyword: " + w + " and tf-idf value: " + str(v) + "\n")
        else:
            p.add_keyword(abb)
            jjj = 1
            key_word_file.write("brand name: " + p.get_brand() + " abbreviation word: " + abb + "\n")
        #check provider name
        abb = check_abbreviation(p.get_provider_name())
        if abb == "0":
            string_index = name_set.index(p.get_provider_name())   
            target_tfidf_values = result[string_index].toarray()[0]
            feature_names = tfidf.get_feature_names_out()
            i = 0
            for word, value in zip(feature_names, target_tfidf_values):
                if value >= 0.7:  
                    i = 1
                    if word not in filtered_words:
                        p.add_keyword(word)
                        jjj = 1
                        key_word_file.write("provider name: " + p.get_provider_name() + " keyword: " + word + " and tf-idf value: " + str(value) + "\n")
            if i == 0:
                w = ""
                v = 0
                for word, value in zip(feature_names, target_tfidf_values):
                    if value > v:  
                        v = value
                        w = word
                if w not in filtered_words:
                    p.add_keyword(w)
                    jjj = 1
                    key_word_file.write("provider name: " + p.get_provider_name() + " keyword: " + w + " and tf-idf value: " + str(v) + "\n")
        else:
            p.add_keyword(abb)
            jjj = 1
            key_word_file.write("provider name: " + p.get_provider_name() + " abbreviation word: " + abb + "\n")
        #check holding company:
        abb = check_abbreviation(p.get_holding_company())
        if abb == "0":
            string_index = name_set.index(p.get_holding_company())   
            target_tfidf_values = result[string_index].toarray()[0]
            feature_names = tfidf.get_feature_names_out()
            i = 0
            for word, value in zip(feature_names, target_tfidf_values):
                if value >= 0.7:  
                    i = 1
                    if word not in filtered_words:
                        p.add_keyword(word)
                        jjj = 1
                        key_word_file.write("holding company name: " + p.get_holding_company() + " keyword: " + word + " and tf-idf value: " + str(value) + "\n")
            if i == 0:
                w = ""
                v = 0
                for word, value in zip(feature_names, target_tfidf_values):
                    if value > v:  
                        v = value
                        w = word
                if w not in filtered_words:
                    p.add_keyword(w)
                    jjj = 1
                    key_word_file.write("holding company name: " + p.get_holding_company() + " keyword: " + w + " and tf-idf value: " + str(v) + "\n")
        else:
            p.add_keyword(abb)
            jjj = 1
            key_word_file.write("holding company name: " + p.get_holding_company() + " abbreviation word: " + abb + "\n")
        if jjj == 0:
            with open(provider_no_keyword_path, "w") as f:
                f.write(f"brand: {p.get_brand()}, provider: {p.get_provider_name()}, holding_company: {p.get_holding_company()}")


print("---------------------------------------------------")
for p in provider_set:
    main_set = p.get_keywords()
    for i in main_set:
        keyword_set.append(i)
for k in keyword_set:
    print(f'{k}, ', end="")

keyword_set = list(set(keyword_set))
with open(keywords_file, "w") as file:
    for i in keyword_set:
        #print(i)
        file.write(i + "\n")


