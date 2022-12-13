from sklearn import tree
import pickle
import matplotlib.pyplot as plt

# Load trained model
with open('decision_tree.pkl', 'rb') as f:
    clf = pickle.load(f)

feature_names = ["mentions",
                 "citations",
                 "authored_count",
                 "authored_count_false",
                 "authored_count_true",
                 "authored_count_other",
                 "authored_count_false_ratio",
                 "authored_count_true_ratio",
                 "authored_count_other_ratio",
                 "reliable"]
class_names = ["TRUE", "FALSE", "NEITHER"]

plt.figure(figsize=(75, 30))
tree.plot_tree(clf, fontsize=15, feature_names=feature_names, class_names=class_names)
plt.savefig("decision_tree.pdf")
