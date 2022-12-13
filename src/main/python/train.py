import numpy as np
import pickle
from SPARQLWrapper import SPARQLWrapper, JSON
from utils import parse_results
from sklearn.tree import DecisionTreeClassifier


sparql = SPARQLWrapper("https://data.gesis.org/claimskg/sparql")

# Training
sparql.setQuery("""
PREFIX itsrdf:<https://www.w3.org/2005/11/its/rdf#>
PREFIX schema:<http://schema.org/>
PREFIX dbr:<http://dbpedia.org/resource/>

SELECT ?claim ?groundTruth ?authoredCountFalse ?authoredCountTrue ?authoredCountOther ?mentions ?citations
WHERE { 
    ?claim a schema:CreativeWork ; 
           schema:datePublished ?date 
    # only claims earlier than 2022
    FILTER(year(?date)<2022)
    # count mentions
    {
        OPTIONAL{
            SELECT ?claim (COUNT(?mention) AS ?mentions) WHERE {
                ?claim schema:mentions ?mention
            } GROUP BY ?claim
        }
    }
    # count citations
    {
        OPTIONAL{
            SELECT ?claim (COUNT(?citation) AS ?citations) WHERE {
                ?claim schema:citation ?citation
            } GROUP BY ?claim
        }
    }
    # count authored false/true/other
    {
        SELECT ?claim (SUM(?authoredCountFalse) AS ?authoredCountFalse) (SUM(?authoredCountTrue) AS ?authoredCountTrue) (SUM(?authoredCountOther) AS ?authoredCountOther) WHERE {
            ?claim schema:author/^schema:author ?authoredClaims .
            # make sure current claim is not counted
            FILTER(STR(?authoredClaims)!=STR(?claim))
            ?authoredClaims ^schema:itemReviewed/schema:reviewRating ?reviewRating .
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 1, 0) AS ?authoredCountFalse)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 0) AS ?authoredCountTrue)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 1, 0) AS ?authoredCountOther)
        } GROUP BY ?claim
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

print("Executing train query")
results = sparql.query().convert()

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

SELECT ?claim ?groundTruth ?authoredCountFalse ?authoredCountTrue ?authoredCountOther ?mentions ?citations
WHERE { 
    ?claim a schema:CreativeWork ; 
           schema:datePublished ?date 
    # only claims earlier than 2022
    FILTER(year(?date)>=2022)
    # count mentions
    {
        OPTIONAL{
            SELECT ?claim (COUNT(?mention) AS ?mentions) WHERE {
                ?claim schema:mentions ?mention
            } GROUP BY ?claim
        }
    }
    # count citations
    {
        OPTIONAL{
            SELECT ?claim (COUNT(?citation) AS ?citations) WHERE {
                ?claim schema:citation ?citation
            } GROUP BY ?claim
        }
    }
    # count authored false/true/other
    {
        SELECT ?claim (SUM(?authoredCountFalse) AS ?authoredCountFalse) (SUM(?authoredCountTrue) AS ?authoredCountTrue) (SUM(?authoredCountOther) AS ?authoredCountOther) WHERE {
            ?claim schema:author/^schema:author ?authoredClaims .
            # make sure current claim is not counted
            FILTER(STR(?authoredClaims)!=STR(?claim))
            ?authoredClaims ^schema:itemReviewed/schema:reviewRating ?reviewRating .
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_FALSE", 1, 0) AS ?authoredCountFalse)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_TRUE", 1, 0) AS ?authoredCountTrue)
            BIND(IF(STR(?reviewRating)="http://data.gesis.org/claimskg/rating/normalized/claimskg_OTHER", 1, 0) AS ?authoredCountOther)
        } GROUP BY ?claim
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

print("Executing validation query")
results = sparql.query().convert()

print("Parsing validation query results")
X_val, y_val = parse_results(results)

print("Predicting validation results")
result = clf.predict(X_val)

print("Validation accuracy: ", np.array(result == y_val).sum()/result.size)

