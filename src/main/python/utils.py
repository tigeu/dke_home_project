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
        authored_count_false = int(result['countFalse']['value'])
        authored_count_true = int(result['countTrue']['value'])
        authored_count_other = int(result['countOther']['value'])
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


def count_ground_truth_claims(author_results, claims=[]):
    count_false = 0
    count_true = 0
    count_other = 0
    for result in author_results['results']['bindings']:
        current_claim = result['claim']['value']

        # don't count claims from test set
        if current_claim in claims:
            continue

        if 'groundTruth' in result:
            ground_truth = int(result['groundTruth']['value'])
            if ground_truth == 0:
                count_false += 1
            elif ground_truth == 1:
                count_true += 1
            elif ground_truth == 2:
                count_other += 1

    return count_false, count_true, count_other
