import spacy
from re import sub

nlp = spacy.load('en_core_web_sm')

blacklisted_words = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN"]

def get_occurences(raw_data, minimum_occurences=2, blacklisted_words=blacklisted_words):
    if raw_data == []:
        return []

    filtered_data = sub(r"\[.+?\]|\(.+?\)", ' ', "\n".join([item[0] for item in raw_data]).replace("(*)", " ")).replace("  ", " ").replace("  ", " ").replace('"', "")

    doc = nlp(filtered_data)

    ents = [ent.text.upper() for ent in doc.ents]

    ents_set = set(ents)

    ent_occurences = []

    counts = []

    for ent in ents_set:
        if ent in blacklisted_words:
            continue

        filtered_ent = ent.removeprefix("THE").removeprefix("THIS").removesuffix("'S")

        count = ents.count(ent)
        ent_occurences.append({"Term": ent, "Count": count})
        counts.append(count)

    sorted_occurences = sorted(ent_occurences, key=lambda d: d['Count'], reverse=True)

    filtered_occurences = []

    for occurence in sorted_occurences:
        if occurence['Count'] >= minimum_occurences:
            filtered_occurences.append(occurence)
    
    return filtered_occurences