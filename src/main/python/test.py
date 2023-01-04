import pickle
import csv
from SPARQLWrapper import SPARQLWrapper, JSON

from utils import parse_results, count_ground_truth_claims

# Load trained model
print("Loading trained decision tree")
with open('decision_tree.pkl', 'rb') as f:
    clf = pickle.load(f)

# Load test IDs
claims = []
print("Loading test ids")
with open("../../../test_data/test_ids.csv", newline='') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=' ', quotechar='|')
    for claim in csv_reader:
        claims.append(claim[0])

claims_count = len(claims)
concat_claims = '"' + '", "'.join(claims) + '"'

# Test
sparql = SPARQLWrapper("https://data.gesis.org/claimskg/sparql")

query = """
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT ?claim ?text ?author ?mentions ?citations
WHERE {{
    ?claim a schema:CreativeWork ; 
           schema:text ?text
    # only use current claim
    FILTER(STR(?claim)="{0}")
    OPTIONAL{{?claim schema:author ?author}}
    # count mentions
    OPTIONAL{{
        SELECT ?claim (COUNT(?mention) AS ?mentions) WHERE {{
            ?claim schema:mentions ?mention
        }} GROUP BY ?claim
    }}
    # count citations
    OPTIONAL{{
        SELECT ?claim (COUNT(?citation) AS ?citations) WHERE {{
            ?claim schema:citation ?citation
        }} GROUP BY ?claim
    }}
}}
"""

author_query = """
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT ?claim ?groundTruth
WHERE {{
    ?claim a schema:CreativeWork ; 
           schema:author ?author 
    FILTER(STR(?author)="{0}")
    # only use claims that have a FALSE, TRUE, or OTHER review
    ?claim ^schema:itemReviewed ?review .
    ?review schema:reviewRating ?reviewRating
    FILTER(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER")
    # bind FALSE to 0, TRUE to 1, OTHER to 2
    BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 0, 
        IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 
            IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 2, -1))) AS ?groundTruth)
}}
"""

print("Executing test query")
X_test = []
claim_data = []
for index, claim in enumerate(claims):
    print(f"Processing {index+1}/{claims_count}")
    formatted_query = query.format(claim)
    sparql.setQuery(formatted_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # get author of current query
    author = ""
    for result in results['results']['bindings']:
        if 'author' in result:
            author = result['author']['value']

    if author:
        formatted_author_query = author_query.format(author)
        sparql.setQuery(formatted_author_query)
        sparql.setReturnFormat(JSON)
        author_results = sparql.query().convert()

        count_false, count_true, count_other = count_ground_truth_claims(author_results, claims)
    else:
        count_false = 0
        count_true = 0
        count_other = 0

    # add to results
    for result in results['results']['bindings']:
        result['countFalse'] = {'value': count_false}
        result['countTrue'] = {'value': count_true}
        result['countOther'] = {'value': count_other}

    X, data = parse_results(results, test=True)

    X_test.extend(X)
    claim_data.extend(data)

print("Predicting test results")
predictions = clf.predict(X_test)

lines = ""
print(f"Claims: {len(claim_data)}, Predictions: {len(predictions)}")
for claim, prediction in zip(claim_data, predictions):
    claim_id, claim_text = claim
    prediction_label = "FALSE"
    if prediction == 1:
        prediction_label = "TRUE"
    elif prediction == 2:
        prediction_label = "NEITHER"

    line = f'{claim_id},"test",{prediction_label}\n'
    lines += line

print("Saving results to csv")
with open("../../../output_data/predictions.csv", "w") as csv_file:
    csv_file.write(lines)
