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
variables = results['head']['vars']

# filter non english
# mentions, citations
true_claims = 0
true_claims_citations = 0
true_claims_mentions = 0
false_claims = 0
false_claims_citations = 0
false_claims_mentions = 0
other_claims = 0
other_claims_citations = 0
other_claims_mentions = 0
for result in results['results']['bindings']:
    if int(result['groundtruth']['value']) == 0:
        false_claims += 1
        false_claims_citations += int(result['citations']['value'])
        false_claims_mentions += int(result['mentions']['value'])
    elif int(result['groundtruth']['value']) == 1:
        true_claims += 1
        true_claims_citations += int(result['citations']['value'])
        true_claims_mentions += int(result['mentions']['value'])
    else:
        other_claims += 1
        other_claims_citations += int(result['citations']['value'])
        other_claims_mentions += int(result['mentions']['value'])

print("Avg false claim citations: " + str(false_claims_citations/false_claims))
print("Avg true claim citations: " + str(true_claims_citations/true_claims))
print("Avg other claim citations: " + str(other_claims_citations/other_claims))

print("Avg false claim mentions: " + str(false_claims_mentions/false_claims))
print("Avg true claim mentions: " + str(true_claims_mentions/true_claims))
print("Avg other claim mentions: " + str(other_claims_mentions/other_claims))
