from sklearn import tree
import pickle
import matplotlib.pyplot as plt

# Load trained model
with open('decision_tree.pkl', 'rb') as f:
    clf = pickle.load(f)

feature_names = ["mentions",
                 "citations",
                 "count",
                 "count_false",
                 "count_true",
                 "count_other",
                 "false_ratio",
                 "true_ratio",
                 "other_ratio",
                 "reliable"]
class_names = ["TRUE", "FALSE", "NEITHER"]

plt.figure(figsize=(500, 50))
tree.plot_tree(clf, fontsize=10, feature_names=feature_names, class_names=class_names)
plt.savefig("decision_tree.pdf")
