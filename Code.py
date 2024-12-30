# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1_71XWJwplLx0qCNoiRQ2V-ZKIB5cHeY1
"""

# Étape 1: Installer les bibliothèques nécessaires
# Exécutez cette cellule pour installer les dépendances
!pip install transformers datasets torch pandas scikit-learn

import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

# Étape 2: Télécharger le dataset depuis GitHub
# Télécharger directement "goodbooks-10k.csv"
!wget https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv -O goodbooks-10k.csv

# Charger les données
books_df = pd.read_csv("goodbooks-10k.csv")
print(books_df.columns)

# Garder uniquement les colonnes nécessaires
books_df = books_df[["book_id", "title", "authors", "average_rating", "language_code", "work_text_reviews_count"]]

#  Étape 3: Prétraitement des données
# Combiner "title" et "work_text_reviews_count" comme entrée, et "average_rating" comme label
books_df = books_df.dropna()
books_df["text"] = books_df["title"] + " - " + books_df["work_text_reviews_count"].astype(str)
books_df["label"] = (books_df["average_rating"] >= 4.0).astype(int)  # Label 1 pour les livres bien notés

# Séparer les données en train et test
train_texts, test_texts, train_labels, test_labels = train_test_split(
    books_df["text"].tolist(), books_df["label"].tolist(), test_size=0.2, random_state=42
)

# Étape 4: Préparer le dataset avec Hugging Face
def preprocess_function(examples):
    return tokenizer(examples["text"], truncation=True, padding=True, max_length=512)

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

train_dataset = Dataset.from_dict({"text": train_texts, "label": train_labels}).map(preprocess_function, batched=True)
test_dataset = Dataset.from_dict({"text": test_texts, "label": test_labels}).map(preprocess_function, batched=True)

# Étape 5: Charger un modèle pré-entraîné
model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2)

from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="steps",  # Evaluation plus flexible
    eval_steps=500,  # Evaluer toutes les 500 étapes
    learning_rate=3e-5,  # Légèrement plus grand pour convergence rapide
    per_device_train_batch_size=16,  # Augmenté pour traiter plus de données à chaque étape
    per_device_eval_batch_size=16,  # Aligné avec la taille de lot d'entraînement
    num_train_epochs=2,  # Réduction à 2 époques
    weight_decay=0.01,  # Légère augmentation pour régularisation
    logging_dir="./logs",
    logging_steps=100,  # Réduction des interruptions fréquentes
    save_steps=1000,  # Sauvegarde moins fréquente
    save_strategy="steps",
    load_best_model_at_end=True,
    fp16=True  # Utiliser la précision mixte pour accélérer sur GPU
)

# Étape 7: Créer un Trainer pour l'entraînement
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    tokenizer=tokenizer,
)

# Étape 8: Entraîner le modèle
trainer.train()

# Étape 9: Évaluer le modèle
results = trainer.evaluate()
print("Résultats de l'évaluation:", results)

# Étape 10: Sauvegarder le modèle
trainer.save_model("./recommender_model")

# Étape 11: Tester le système de recommandation
# Exemple d'entrée utilisateur
user_input = "Fantasy - A magical world full of adventures."
inputs = tokenizer(user_input, return_tensors="pt", truncation=True, padding=True, max_length=512)
outputs = model(**inputs)
prediction = outputs.logits.argmax(-1).item()
print("Recommandation pour cette description: ", "Recommandé" if prediction == 1 else "Non recommandé")

user_input = "THE SHARDS"
inputs = tokenizer(user_input, return_tensors="pt", truncation=True, padding=True, max_length=512)
outputs = model(**inputs)
prediction = outputs.logits.argmax(-1).item()
print("Recommandation pour cette description: ", "Recommandé" if prediction == 1 else "Non recommandé")