import numpy as np
from SPARQLWrapper import SPARQLWrapper, JSON

from sklearn.tree import DecisionTreeClassifier


def parse_results(results):
    X = []
    y = []
    for result in results['results']['bindings']:
        ground_truth = int(result['groundTruth']['value'])
        authored_count_false = int(result['authoredCountFalse']['value'])
        authored_count_true = int(result['authoredCountTrue']['value'])
        authored_count_other = int(result['authoredCountOther']['value'])
        authored_count = authored_count_false + authored_count_true + authored_count_other
        authored_count_false_ratio = authored_count_false / authored_count
        authored_count_true_ratio = authored_count_true / authored_count
        authored_count_other_ratio = authored_count_other / authored_count
        reliable = authored_count_false_ratio < 0.1 and (
                authored_count_true_ratio > 0 or authored_count_other_ratio > 0)
        X.append([authored_count,
                  authored_count_false,
                  authored_count_true,
                  authored_count_other,
                  authored_count_false_ratio,
                  authored_count_true_ratio,
                  authored_count_other_ratio,
                  reliable])
        y.append(ground_truth)

    return X, y


sparql = SPARQLWrapper("https://data.gesis.org/claimskg/sparql")

sparql.setQuery("""
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT ?claim ?text ?groundTruth ?authoredCountFalse ?authoredCountTrue ?authoredCountOther
WHERE { 
    ?claim a schema:CreativeWork ; 
           schema:datePublished ?date
    # only claims earlier than 2022
    FILTER(year(?date)<2022)
    ?claim schema:author ?author .
    # count authored false/true/other
    {
        SELECT ?author (SUM(?authoredCountFalse) AS ?authoredCountFalse) (SUM(?authoredCountTrue) AS ?authoredCountTrue) (SUM(?authoredCountOther) AS ?authoredCountOther) WHERE {
            ?author ^schema:author/^schema:itemReviewed/schema:reviewRating ?reviewRating .
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 1, 0) AS ?authoredCountFalse)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 0) AS ?authoredCountTrue)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 1, 0) AS ?authoredCountOther)
        } GROUP BY ?author
    }
    # only use claims that have a FALSE, TRUE, or OTHER review
    ?claim ^schema:itemReviewed ?review .
    ?review schema:reviewRating ?reviewRating
    FILTER(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER")
    # bind FALSE to 0, TRUE to 1, OTHER to 2
    BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 0, 
             IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 
                 IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 2, -1))) AS ?groundTruth)
}
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

X_train, y_train = parse_results(results)

print("Train length: ", len(y_train))

clf = DecisionTreeClassifier(max_depth=4)
clf = clf.fit(X_train, y_train)

sparql.setQuery("""
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT ?claim ?text ?groundTruth ?authoredCountFalse ?authoredCountTrue ?authoredCountOther
WHERE { 
    ?claim a schema:CreativeWork ; 
           schema:datePublished ?date
    # only claims earlier than 2022
    FILTER(year(?date)>=2022)
    ?claim schema:author ?author .
    # count authored false/true/other
    {
        SELECT ?author (SUM(?authoredCountFalse) AS ?authoredCountFalse) (SUM(?authoredCountTrue) AS ?authoredCountTrue) (SUM(?authoredCountOther) AS ?authoredCountOther) WHERE {
            ?author ^schema:author/^schema:itemReviewed/schema:reviewRating ?reviewRating .
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 1, 0) AS ?authoredCountFalse)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 0) AS ?authoredCountTrue)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 1, 0) AS ?authoredCountOther)
        } GROUP BY ?author
    }
    # only use claims that have a FALSE, TRUE, or OTHER review
    ?claim ^schema:itemReviewed ?review .
    ?review schema:reviewRating ?reviewRating
    FILTER(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER")
    # bind FALSE to 0, TRUE to 1, OTHER to 2
    BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 0, 
             IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 
                 IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 2, -1))) AS ?groundTruth)
} 
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

X_val, y_val = parse_results(results)

print("Val length: ", len(y_val))

result = clf.predict(X_val)
print("Result: ", result)
print("Groundtruth: ", y_val)
print(np.array(result == y_val).sum()/result.size)
