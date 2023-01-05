# DKE 2022 Home Project
This repository contains the home project for the Data and Knowledge Engineering class 2022 at Heinrich Heine University.
The project exercise can be completed at home, using the expertise and skill sets acquired in the DKE 2022 lecture.
Use this repository to prepare your solution.


## Folder Structure

- **assignment**: contains a more detailed description of the task and the required output. 
- **src**: add your code here in the suitable subfolder(s) (depending on whether you use Python or Java). 
- **test_data**:  the test data will be added to this folder (file _test\_ids.csv_). Please refer to the task description in the assignment folder for information on the format. The dummy_ids.csv file contains dummy data in the required format. 
- **output_data**: folder that must be populated with the results of the home project (file _predictions.csv_). Please refer to the task description in the assignment folder for information on the format. The file dummy_predictions.csv contains dummy data in the required format.
- **eval**: contains the evaluation script and gold standard file. Run  `python3 eval.py` to compute the score of your model (compares your predictions in output\_data /predictions.csv to the gold standard). 


## Output file
output_data/predictions.csv

## Output of the evaluation script
Accuracy: 0.54
(macro) Precision: 0.53
(macro) Recall: 0.48

(also saved in "evaluation_output.txt")

## Training explanation
First I query 1000 claims, their authors, the amount of mentions and citations from the endpoint using this query:
```
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
}} 
```
The author is required for the next query to find out whether the author tends to write false, true or neither claims. If they publish false news more often it is likely that their next claim is false, too. The mentions and citations could also be interesting, as e.g. true claims might have more citations than false ones.
After that I Loop through all the claims and execute a specific additional query getting all claims the author published together with its ground truth data. In the code it is ensured that no review rating from the test set is used.
```
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
```

## Testing explanation
The testing follows the same procedure as the training, with the following, modified queries:
```
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
```
```
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
```

## Train model
The model can be trained by executing "src/main/python/train.py"

## Apply model
The model can be applied by executing "src/main/python/test.py"
