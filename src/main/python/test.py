import pickle
import csv
from sklearn import tree
from SPARQLWrapper import SPARQLWrapper, JSON

from utils import parse_results

# Load trained model
print("Loading trained decision tree")
with open('decision_tree.pkl', 'rb') as f:
    clf = pickle.load(f)

# Load test IDs
claims = []
print("Loading test ids")
with open("../../../test_data/dummy_ids.csv", newline='') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=' ', quotechar='|')
    for claim in csv_reader:
        claims.append(claim[0])

concat_claims = '"' + '", "'.join(claims) + '"'

# Test
sparql = SPARQLWrapper("https://data.gesis.org/claimskg/sparql")

sparql.setQuery("""
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT ?claim ?text ?authoredCountFalse ?authoredCountTrue ?authoredCountOther ?mentions ?citations
WHERE {{
    ?claim a schema:CreativeWork ; 
           schema:text ?text
    FILTER(STR(?claim) in ({0}))
    # count mentions
    {{
        OPTIONAL{{
            SELECT ?claim (COUNT(?mention) AS ?mentions) WHERE {{
                ?claim schema:mentions ?mention
            }} GROUP BY ?claim
        }}
    }}
    # count citations
    {{
        OPTIONAL{{
            SELECT ?claim (COUNT(?citation) AS ?citations) WHERE {{
                ?claim schema:citation ?citation
            }} GROUP BY ?claim
        }}
    }}
    ?claim schema:author ?author .
    # count authored false/true/other
    {{
        SELECT ?claim (SUM(?authoredCountFalse) AS ?authoredCountFalse) (SUM(?authoredCountTrue) AS ?authoredCountTrue) (SUM(?authoredCountOther) AS ?authoredCountOther) WHERE {{
            ?claim schema:author/^schema:author ?authoredClaims .
            # make sure current claim is not counted
            FILTER(STR(?authoredClaims)!=STR(?claim))
            # make sure other claims in test set are not counted
            FILTER(STR(?authoredClaims) not in ({0}))
            ?authoredClaims ^schema:itemReviewed/schema:reviewRating ?reviewRating .
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 1, 0) AS ?authoredCountFalse)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 0) AS ?authoredCountTrue)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 1, 0) AS ?authoredCountOther)
        }} GROUP BY ?claim
    }}
}}
""".format(concat_claims))

sparql.setReturnFormat(JSON)

print("Executing test query")
results = sparql.query().convert()

print("Parsing test query results")
X_test, claim_data = parse_results(results, test=True)

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

    line = f'{claim_id},""{claim_text}"",{prediction_label}\n'
    lines += line

print("Saving results to csv")
with open("../../../output_data/predictions.csv", "w", encoding='utf-8') as csv_file:
    csv_file.write(lines)
