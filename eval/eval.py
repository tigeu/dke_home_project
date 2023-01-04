from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
import csv
import os

def getIdsNLabels(filename, labelIndex=1):
    with open(filename, "r") as csvfile:
        reader = csv.reader(csvfile)
        return { row[0] : row[labelIndex] for row in reader }

#predictions and gold standard IDs may not be in the same order
def getY(gold, predicted):
    y_true = []
    y_pred = []
    test_ids = list(gold.keys())
    for test_id in test_ids:
        y_true.append(gold.get(test_id))
        y_pred.append(predicted.get(test_id))
    return (y_true, y_pred)

def getAccuracy(y_true, y_pred):
    return accuracy_score(y_true, y_pred, normalize=True)

def getRecall(y_true, y_pred):
    return recall_score(y_true, y_pred, average='macro')

def getPrecision(y_true, y_pred):
    return precision_score(y_true, y_pred, average='macro')

if __name__=="__main__":
    gold = getIdsNLabels(os.path.join(os.path.dirname(os.path.realpath(__file__)), "gold.csv"))
    predicted = getIdsNLabels(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../output_data/predictions.csv"), 2)
    y_true, y_predicted = getY(gold, predicted)
    try:
        print("Accuracy: %1.2f" %getAccuracy(y_true, y_predicted))
        print("(macro) Precision: %1.2f" %getPrecision(y_true, y_predicted))
        print("(macro) Recall: %1.2f" %getRecall(y_true, y_predicted))
    except ValueError as e:
        import sys
        sys.stderr.write(str(e) + "\n")
        sys.stderr.write("Please check your output file, e.g. does it contain predictions for every claim ID in the test set?")
