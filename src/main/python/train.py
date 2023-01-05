import numpy as np
import pickle
from SPARQLWrapper import SPARQLWrapper, JSON
from utils import parse_results, count_ground_truth_claims
from sklearn.tree import DecisionTreeClassifier


sparql = SPARQLWrapper("https://data.gesis.org/claimskg/sparql")

# Training
sparql.setQuery("""
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT ?claim ?text ?author ?mentions ?citations ?groundTruth
WHERE {{
    ?claim a schema:CreativeWork ; 
           schema:text ?text .
    # only use claims that have a FALSE, TRUE, or OTHER review
    ?claim ^schema:itemReviewed ?review .
    # only claims reviewed earlier than 2022
    ?review schema:datePublished ?datePublished
    FILTER(year(?datePublished)<2022)
    ?review schema:reviewRating ?reviewRating
    FILTER(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER")
    # bind FALSE to 0, TRUE to 1, OTHER to 2
    BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 0, 
        IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 
            IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 2, -1))) AS ?groundTruth)
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
}} LIMIT 100
""")
sparql.setReturnFormat(JSON)

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
    # only claims reviewed earlier than 2022
    ?review schema:datePublished ?datePublished
    FILTER(year(?datePublished)<2022)
    ?review schema:reviewRating ?reviewRating
    FILTER(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER")
    # bind FALSE to 0, TRUE to 1, OTHER to 2
    BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 0, 
        IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 
            IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 2, -1))) AS ?groundTruth)
}}
"""

print("Executing train query")
results = sparql.query().convert()
claims_count = len(results['results']['bindings'])
for index, result in enumerate(results['results']['bindings']):
    claim = result['claim']['value']
    print(f"Processing {index + 1}/{claims_count}: {claim}")
    # get author of current query
    author = ""
    if 'author' in result:
        author = result['author']['value']

    if author:
        formatted_author_query = author_query.format(author)
        sparql.setQuery(formatted_author_query)
        sparql.setReturnFormat(JSON)
        author_results = sparql.query().convert()

        count_false, count_true, count_other = count_ground_truth_claims(author_results)
    else:
        count_false = 0
        count_true = 0
        count_other = 0

    # add to results
    result['countFalse'] = {'value': count_false}
    result['countTrue'] = {'value': count_true}
    result['countOther'] = {'value': count_other}

print("Parsing train query results")
X_train, y_train = parse_results(results)

print("Training classifier")
clf = DecisionTreeClassifier(max_depth=8)
clf = clf.fit(X_train, y_train)

# Save trained model
print("Saving trained model")
with open('decision_tree.pkl', 'wb') as f:
    pickle.dump(clf, f)

# Validation
sparql.setQuery("""
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT ?claim ?text ?author ?mentions ?citations ?groundTruth
WHERE {{
    ?claim a schema:CreativeWork ; 
           schema:text ?text .
    # only use claims that have a FALSE, TRUE, or OTHER review
    ?claim ^schema:itemReviewed ?review .
    # only claims reviewed later than 2022
    ?review schema:datePublished ?datePublished
    FILTER(year(?datePublished)>=2022)
    ?review schema:reviewRating ?reviewRating
    FILTER(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER")
    # bind FALSE to 0, TRUE to 1, OTHER to 2
    BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 0, 
        IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 
            IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 2, -1))) AS ?groundTruth)
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
}} LIMIT 100
""")
sparql.setReturnFormat(JSON)

print("Executing validation query")
results = sparql.query().convert()
claims_count = len(results['results']['bindings'])
for index, result in enumerate(results['results']['bindings']):
    claim = result['claim']['value']
    print(f"Processing {index + 1}/{claims_count}: {claim}")
    # get author of current query
    author = ""
    if 'author' in result:
        author = result['author']['value']

    if author:
        formatted_author_query = author_query.format(author)
        sparql.setQuery(formatted_author_query)
        sparql.setReturnFormat(JSON)
        author_results = sparql.query().convert()

        count_false, count_true, count_other = count_ground_truth_claims(author_results)
    else:
        count_false = 0
        count_true = 0
        count_other = 0

    # add to results
    result['countFalse'] = {'value': count_false}
    result['countTrue'] = {'value': count_true}
    result['countOther'] = {'value': count_other}

print("Parsing validation query results")
X_val, y_val = parse_results(results)

print("Predicting validation results")
result = clf.predict(X_val)

print("Validation accuracy: ", np.array(result == y_val).sum()/result.size)
