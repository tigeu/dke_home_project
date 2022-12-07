import numpy as np
from sklearn.datasets import load_iris
from sklearn import tree
from SPARQLWrapper import SPARQLWrapper, JSON, XML, N3, RDF

sparql = SPARQLWrapper("https://data.gesis.org/claimskg/sparql")

sparql.setQuery("""
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT DISTINCT ?claim ?text ?groundtruth ?mentions ?citations
WHERE { 
    ?claim a schema:CreativeWork ; 
           schema:datePublished ?date 
    # only claims earlier than 2022
    FILTER(year(?date)<2022) 
    ?claim schema:text ?text 
    # only english 
    FILTER(lang(?text)="en")
    ?claimReview schema:itemReviewed ?claim ;
                 schema:reviewRating ?reviewRating 
    # count mentions
    {
        SELECT ?claim (COUNT(?mention) AS ?mentions) WHERE {
            ?claim schema:mentions ?mention
        } GROUP BY ?claim
    }
    # count citations
    {
        SELECT ?claim (COUNT(?citation) AS ?citations) WHERE {
            ?claim schema:citation ?citation
        } GROUP BY ?claim
    }
    # only use claims that have a FALSE, TRUE, or OTHER review
    FILTER(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER")
    # bind FALSE to 0, TRUE to 1, OTHER to 2
    BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 0, 
             IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 
                 IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 2, -1))) AS ?groundtruth)
} 
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# filter non english
true_claims = 0
true_claims_citations = 0
true_claims_mentions = 0
false_claims = 0
false_claims_citations = 0
false_claims_mentions = 0
other_claims = 0
other_claims_citations = 0
other_claims_mentions = 0

X_train = []
y_train = []
for result in results['results']['bindings']:
    groundtruth = int(result['groundtruth']['value'])
    citations = int(result['citations']['value'])
    mentions = int(result['mentions']['value'])
    X_train.append([citations, mentions])
    y_train.append(groundtruth)
    if groundtruth == 0:
        false_claims += 1
        false_claims_citations += citations
        false_claims_mentions += mentions
    elif groundtruth == 1:
        true_claims += 1
        true_claims_citations += citations
        true_claims_mentions += mentions
    else:
        other_claims += 1
        other_claims_citations += citations
        other_claims_mentions += mentions

print("Avg false claim citations: " + str(false_claims_citations/false_claims))
print("Avg true claim citations: " + str(true_claims_citations/true_claims))
print("Avg other claim citations: " + str(other_claims_citations/other_claims))

print("Avg false claim mentions: " + str(false_claims_mentions/false_claims))
print("Avg true claim mentions: " + str(true_claims_mentions/true_claims))
print("Avg other claim mentions: " + str(other_claims_mentions/other_claims))

clf = tree.DecisionTreeClassifier()
clf = clf.fit(X_train, y_train)

sparql.setQuery("""
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT DISTINCT ?claim ?text ?groundtruth ?mentions ?citations
WHERE { 
    ?claim a schema:CreativeWork ; 
           schema:datePublished ?date 
    # only claims earlier than 2022
    FILTER(year(?date)>=2022) 
    ?claim schema:text ?text 
    # only english 
    FILTER(lang(?text)="en")
    ?claimReview schema:itemReviewed ?claim ;
                 schema:reviewRating ?reviewRating 
    # count mentions
    {
        SELECT ?claim (COUNT(?mention) AS ?mentions) WHERE {
            ?claim schema:mentions ?mention
        } GROUP BY ?claim
    }
    # count citations
    {
        SELECT ?claim (COUNT(?citation) AS ?citations) WHERE {
            ?claim schema:citation ?citation
        } GROUP BY ?claim
    }
    # only use claims that have a FALSE, TRUE, or OTHER review
    FILTER(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE" || STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER")
    # bind FALSE to 0, TRUE to 1, OTHER to 2
    BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 0, 
             IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 
                 IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 2, -1))) AS ?groundtruth)
} 
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

X_val = []
y_val = []
for result in results['results']['bindings']:
    groundtruth = int(result['groundtruth']['value'])
    citations = int(result['citations']['value'])
    mentions = int(result['mentions']['value'])
    X_val.append([citations, mentions])
    y_val.append(groundtruth)


result = clf.predict(X_val)
print("Result: ", result)
print("Groundtruth: ", y_val)
print(np.array(result == y_val).sum()/result.size)
