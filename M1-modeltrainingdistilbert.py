# -*- coding: utf-8 -*-
"""ModelTrainingdistilBERT.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/175GZdRtOP-Z6mfDlIgZNOjK-OMhoMYYZ
"""

import torch, os
import pandas as pd
from transformers import pipeline, BertForSequenceClassification, BertTokenizerFast
from torch.utils.data import Dataset
from torch import cuda
device = 'cuda' if cuda.is_available() else 'cpu'

from google.colab import drive
drive.mount('/content/drive')
df_org = pd.read_csv('/content/drive/MyDrive/CodingFiles/BenefitCodingv8.csv')
df_org = df_org.sample(frac=1.0, random_state=42)

labels = df_org['category'].unique().tolist()
labels = [s.strip() for s in labels ]
labels

for key, value in enumerate(labels):
    print(value)

NUM_LABELS= len(labels)

id2label={id:label for id,label in enumerate(labels)}

label2id={label:id for id,label in enumerate(labels)}

label2id

id2label

df_org["labels"]=df_org.category.map(lambda x: label2id[x.strip()])

df_org.head()

df_org.category.value_counts().plot(kind='pie', figsize=(10,10))

tokenizer = BertTokenizerFast.from_pretrained("distilbert/distilbert-base-uncased", max_length=512)

model = BertForSequenceClassification.from_pretrained("distilbert/distilbert-base-uncased", num_labels=NUM_LABELS, id2label=id2label, label2id=label2id)
model.to(device)

SIZE= df_org.shape[0]

train_texts= list(df_org.text[:SIZE//2])

val_texts=   list(df_org.text[SIZE//2:(3*SIZE)//4 ])

test_texts=  list(df_org.text[(3*SIZE)//4:])

train_labels= list(df_org.labels[:SIZE//2])

val_labels=   list(df_org.labels[SIZE//2:(3*SIZE)//4])

test_labels=  list(df_org.labels[(3*SIZE)//4:])
train_texts = [str(text) for text in train_texts]
val_texts = [str(text) for text in val_texts]
test_texts = [str(text) for text in test_texts]

len(train_texts), len(val_texts), len(test_texts)

train_encodings = tokenizer(train_texts, truncation=True, padding=True)
val_encodings  = tokenizer(val_texts, truncation=True, padding=True)
test_encodings = tokenizer(test_texts, truncation=True, padding=True)

class DataLoader(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        # Retrieve tokenized data for the given index
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        # Add the label for the given index to the item dictionary
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):

        return len(self.labels)

train_dataloader = DataLoader(train_encodings, train_labels)

val_dataloader = DataLoader(val_encodings, val_labels)

test_dataset = DataLoader(test_encodings, test_labels)

from transformers import TrainingArguments, Trainer

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def compute_metrics(pred):

    # Extract true labels from the input object
    labels = pred.label_ids

    # Obtain predicted class labels by finding the column index with the maximum probability
    preds = pred.predictions.argmax(-1)

    # Compute macro precision, recall, and F1 score using sklearn's precision_recall_fscore_support function
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='macro')

    # Calculate the accuracy score using sklearn's accuracy_score function
    acc = accuracy_score(labels, preds)

    # Return the computed metrics as a dictionary
    return {
        'Accuracy': acc,
        'F1': f1,
        'Precision': precision,
        'Recall': recall
    }

training_args = TrainingArguments(
    # The output directory where the model predictions and checkpoints will be written
    output_dir='./TTC4900Model',
    do_train=True,
    do_eval=True,
    #  The number of epochs, defaults to 3.0
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    # Number of steps used for a linear warmup
    warmup_steps=100,
    weight_decay=0.01,
    logging_strategy='steps',
   # TensorBoard log directory
    logging_dir='./multi-class-logs',
    logging_steps=50,
    evaluation_strategy="steps",
    eval_steps=50,
    save_strategy="steps",
    fp16=True,
    load_best_model_at_end=True
)

trainer = Trainer(
    # the pre-trained model that will be fine-tuned
    model=model,
     # training arguments that we defined above
    args=training_args,
    train_dataset=train_dataloader,
    eval_dataset=val_dataloader,
    compute_metrics= compute_metrics
)

trainer.train()

q=[trainer.evaluate(eval_dataset=df_org) for df_org in [train_dataloader, val_dataloader, test_dataset]]

pd.DataFrame(q, index=["train","val","test"]).iloc[:,:5]

from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast

def predict(text):

    # Tokenize the input text and move tensors to the GPU if available
    inputs = tokenizer(text, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)

    # Get model output (logits)
    outputs = model(**inputs)

    probs = outputs[0].softmax(1)

    # Get the index of the class with the highest probability
    # argmax() finds the index of the maximum value in the tensor along a specified dimension.
    # By default, if no dimension is specified, it returns the index of the maximum value in the flattened tensor.
    pred_label_idx = probs.argmax()

    # Now map the predicted class index to the actual class label
    # Since pred_label_idx is a tensor containing a single value (the predicted class index),
    # the .item() method is used to extract the value as a scalar
    pred_label = model.config.id2label[pred_label_idx.item()]
   # print("Avaliable classes to code-in \n 1- Fast or immediate results / 2 - Good efficacy or results / 3 - Good safety or higher safety compared to others / 4 - Good side effect profile / 5 - Oral route or tablet formulation / 6 - Easy to use or administer / 7 - Cheap or Affordable / 8 - Long-term or Sustained efficacy / 9 - Improves quality of life / 10 - Other")

    return probs, pred_label_idx, pred_label

# Test with a an example text in Turkish
text = "cheaper than other"
# "Machine Learning itself is moving towards more and more automated"
predict(text)

model_path = "TraineddistilBERTModelv2"
trainer.save_model(model_path)
tokenizer.save_pretrained(model_path)

model_path = "TraineddistilBERTModelv2"

model = BertForSequenceClassification.from_pretrained(model_path)
tokenizer= BertTokenizerFast.from_pretrained(model_path)
nlp= pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
nlp2= pipeline("text-classification", model=model, tokenizer=tokenizer)

nlp("It can significantly improve patients' quality of life.")
nlp2("It can significantly improve patients' quality of life.")

nlp2("best results")

nlp2("less cost than other")

from google.colab import files
import shutil

shutil.make_archive('TraineddistilBERTModelv2', 'zip', 'TraineddistilBERTModelv2')

files.download('TraineddistilBERTModelv2.zip')