import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from imblearn.over_sampling import SMOTE
import xgboost as xgb
from lightgbm import LGBMClassifier
import time
import sys

print("\n\n--- Welcome to AY10 ML - Version 1 ---\n\n")

# Load the dataset
data = pd.read_csv('dataCollection/MLDATA/labeledAnalysis.csv')

features = ['movAvgSizeValue', 'consecutiveGainsValue', 'thresholdGainValue', 'stopLossValue']
X = data[features]
y = data['label']

# Ask the user to choose the labeling method
labeling_method = input("Choose the labeling method (ordinal/binary): ").strip().lower()

if labeling_method == 'binary':
    # Create a binary classification problem
    y = y.apply(lambda x: 0 if x <= 0 else 1)

    # Count the number of each label type
    label_counts = y.value_counts()
    total_labels = len(y)
    label_percentages = {label: (count / total_labels) * 100 for label, count in label_counts.items()}

    print("Label distribution:")
    for label, count in label_counts.items():
        print(f"Label {label}: {count} ({label_percentages[label]:.2f}%)")

elif labeling_method == 'ordinal':
    # Count the number of each specified label type
    specified_labels = [-6, -4, -2, 0, 6, 10]
    label_counts = {label: (y == label).sum() for label in specified_labels}
    total_labels = len(y)
    label_percentages = {label: (count / total_labels) * 100 for label, count in label_counts.items()}

    print("Label distribution:")
    for label, count in label_counts.items():
        print(f"Label {label}: {count} ({label_percentages[label]:.2f}%)")

    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)
else:
    print("Invalid labeling method chosen. Exiting.")
    sys.exit()

# Ask the user to continue or quit
user_input = input("Do you want to continue with the ML process? (y/n): ")
if user_input.lower() != 'y':
    print("Process terminated by the user.")
    sys.exit()

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Apply SMOTE to the training data
smote = SMOTE(random_state=42)
X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)

# Feature scaling
scaler = StandardScaler()
X_train_smote = scaler.fit_transform(X_train_smote)
X_test = scaler.transform(X_test)

# Define the models to be tested with class weights for binary classification
if labeling_method == 'binary':
    models = {
        'Logistic Regression': LogisticRegression(class_weight='balanced'),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'),
        'K-Nearest Neighbors': KNeighborsClassifier(),
        'Naive Bayes': GaussianNB(),
        'Decision Tree': DecisionTreeClassifier(random_state=42, class_weight='balanced'),
        #'Support Vector Machine': SVC(class_weight='balanced'),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42),
        'XGBoost': xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
        'LightGBM': LGBMClassifier(),
        'MLP Classifier': MLPClassifier(random_state=42)
    }
else:
    models = {
        'Logistic Regression': LogisticRegression(),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'K-Nearest Neighbors': KNeighborsClassifier(),
        'Naive Bayes': GaussianNB(),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        #'Support Vector Machine': SVC(),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42),
        'XGBoost': xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
        'LightGBM': LGBMClassifier(),
        'MLP Classifier': MLPClassifier(random_state=42)
    }

# Evaluate each model
results = []

for i, (model_name, model) in enumerate(models.items()):
    print(f"Processing {model_name} ({i+1}/{len(models)})...", file=sys.stderr)
    start_time = time.time()
    model.fit(X_train_smote, y_train_smote)
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    
    if labeling_method == 'binary':
        precision = precision_score(y_test, y_pred, average='binary', zero_division=0)
        recall = recall_score(y_test, y_pred, average='binary', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='binary', zero_division=0)
    else:
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    results.append({
        'Model': model_name,
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1 Score': f1,
        'Training Time (s)': elapsed_time
    })
    print(f"{model_name} completed in {elapsed_time:.2f} seconds.", file=sys.stderr)
    
    # Print confusion matrix
    print(f"Confusion Matrix for {model_name}:\n{confusion_matrix(y_test, y_pred)}", file=sys.stderr)

# Create a DataFrame to display the results
results_df = pd.DataFrame(results)

# Print the results
print(results_df)

# Save the results to a CSV file
results_df.to_csv('model_evaluation_results.csv', index=False)

# Indicate completion
print("Model evaluation completed.", file=sys.stderr)
