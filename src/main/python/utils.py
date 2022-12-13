def parse_results(results, test=False):
    X = []
    y = []
    count = 0
    for result in results['results']['bindings']:
        if "mentions" in result:
            mentions = int(result['mentions']['value'])
        else:
            mentions = 0
        if "citations" in result:
            citations = int(result['citations']['value'])
        else:
            citations = 0
        authored_count_false = int(result['authoredCountFalse']['value'])
        authored_count_true = int(result['authoredCountTrue']['value'])
        authored_count_other = int(result['authoredCountOther']['value'])
        authored_count = authored_count_false + authored_count_true + authored_count_other
        if authored_count == 0:
            authored_count_false_ratio = 0
            authored_count_true_ratio = 0
            authored_count_other_ratio = 0
        else:
            authored_count_false_ratio = authored_count_false / authored_count
            authored_count_true_ratio = authored_count_true / authored_count
            authored_count_other_ratio = authored_count_other / authored_count
        reliable = authored_count_false_ratio < 0.1 and (
                authored_count_true_ratio > 0 or authored_count_other_ratio > 0)
        X.append([mentions,
                  citations,
                  authored_count,
                  authored_count_false,
                  authored_count_true,
                  authored_count_other,
                  authored_count_false_ratio,
                  authored_count_true_ratio,
                  authored_count_other_ratio,
                  reliable])
        if test:
            claim = result['claim']['value']
            text = result['text']['value']
            y.append([claim, text])
        if not test:
            ground_truth = int(result['groundTruth']['value'])
            y.append(ground_truth)

    return X, y
