# -*- coding: utf-8 -*-
"""B21AI027_Lab_Assignment_10

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1qJfjcbZdY0WYQ7czNYncWimPQhNzIXkr
"""

import joblib
import sys
sys.modules['sklearn.externals.joblib'] = joblib
from mlxtend.feature_selection import SequentialFeatureSelector as SFS
import pandas as pd
from sklearn.model_selection import train_test_split
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import torch
import torch.nn as nn
from torch.autograd import Variable
from sklearn.utils import shuffle
from torchsummary import summary

if os.path.exists('abalone.data'):
    print("Already Present")
else:
    os.system("wget https://www.dropbox.com/s/jfiypwq4vxvfy58/abalone.data")

np.random.seed(2)

column_names = ["Sex", "Length", "Diameter", "Height", "Whole weight", "Shucked weight", "Viscera weight", "Shell weight", "Rings"]
df = pd.read_csv("abalone.data", names=column_names)

df

df.isnull().sum()

np.unique(df['Rings'])

df.dtypes

np.unique(df['Sex'])

from sklearn.preprocessing import LabelEncoder

encoder = LabelEncoder()
df["Sex"] = encoder.fit_transform(df["Sex"])

# Print the conversion
print("Conversion for Sex column:")
for i, label in enumerate(encoder.classes_):
    print(f"{label} -> {i}")


encoder = LabelEncoder()
df["Rings"] = encoder.fit_transform(df["Rings"])

df

df.describe()

import seaborn as sns
import pandas as pd

# Bar Plots
for column in df.columns[:-1]:  
    plt.figure()
    if column in ["Length", "Diameter", "Height", "Whole weight", "Shucked weight", "Viscera weight", "Shell weight"]:
        sns.barplot(x=pd.cut(df[column], bins=10), y="Rings", data=df)
    else:
        sns.barplot(x=column, y="Rings", data=df)
    plt.xlabel(column)
    plt.ylabel("Rings")
    plt.show()

sns.histplot(data=df, x="Rings")

# correlation plot
corr = df.corr()
sns.heatmap(corr, annot=True)
plt.show()

from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()

# standardization
for col in df.columns[:-1]:
    df[col] = scaler.fit_transform(df[[col]])

unique_values, counts = np.unique(df["Rings"], return_counts=True)
print("Unique_Values:",unique_values)
print("Counts:",counts)

df.describe()

# threshold for pre-taking class and later adding to train
df_preserved = df.copy(deep=True)
threshold = 3
class_counts = df["Rings"].value_counts()
df_temp = pd.DataFrame()

for cls, count in class_counts.items():
    if count < threshold:
        df_temp = df_temp.append(df[df["Rings"]==cls])

# Drop the rows
df = df.drop(df_temp.index)

# TTS with stratified sampling
X_train, X_test, y_train, y_test = train_test_split(df.iloc[:, :-1], df["Rings"], test_size=0.2, stratify=df["Rings"], random_state=2)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, stratify=y_train, random_state=2)

# Merge df_temp and X_train
X_train = pd.concat([X_train, df_temp.drop(["Rings"], axis=1)])
y_train = pd.concat([y_train, df_temp["Rings"]])

df_temp

X_train

y_train

unique_values, counts = np.unique(y_train, return_counts=True)
print("Class distribution in train set:")
for val, count in zip(unique_values, counts):
    print(f"{val}: {count/len(y_train):.2%}")
    
print()

unique_values, counts = np.unique(y_test, return_counts=True)
print("Class distribution in test set:")
for val, count in zip(unique_values, counts):
    print(f"{val}: {count/len(y_test):.2%}")

num_labels = len(np.unique(df_preserved["Rings"]))
print(num_labels)

# # Apply one-hot encoding
# y_one_hot_train = np.eye(num_labels)[np.array(y_train).astype(int).reshape(1,-1)]
# y_reshaped_train = y_one_hot_train.reshape(-1, num_labels)

# y_one_hot_test = np.eye(num_labels)[np.array(y_test).astype(int).reshape(1,-1)]
# y_reshaped_test = y_one_hot_test.reshape(-1, num_labels)

# y_one_hot_val = np.eye(num_labels)[np.array(y_val).astype(int).reshape(1,-1)]
# y_reshaped_val = y_one_hot_val.reshape(-1, num_labels)

#Create the model
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
class Net(torch.nn.Module):
    def __init__(self, input_dim, num_labels):
        super(Net, self).__init__()
        self.layer_1 = torch.nn.Linear(input_dim, 128)  
        self.activation_1 = torch.nn.Tanh() 
        self.layer_2 = torch.nn.Linear(input_dim, 128) 
        self.activation_2 = torch.nn.Tanh()
        self.layer_3 = torch.nn.Linear(128, num_labels)   
        self.activation_3 = torch.nn.Sigmoid()

    def forward(self, x):
        x1 = x
        x2 = x
        x_1_out = self.activation_1(self.layer_1(x1))      
        x_2_out = self.activation_2(self.layer_2(x2))  
        x = x_1_out+x_2_out                                         
        x = self.activation_3(self.layer_3(x))                
        return x

model = Net(X_train.shape[1],num_labels)
summary(model,X_train.shape)

X_train.shape

def get_accuracy(logit, target, batch_size):
    corrects = (torch.max(logit, 1)[1].view(target.size()).data == target.data).sum()
    accuracy = 100.0 * corrects/batch_size
    return accuracy.item()

optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)
loss_func = torch.nn.CrossEntropyLoss()

import matplotlib.pyplot as plt

batch_size = 8
num_epochs = 250
batch_no = len(X_train) // batch_size

train_loss = []
train_acc = []
val_loss = []
val_acc = []

for epoch in range(num_epochs):
    X_train, y_train = shuffle(X_train, y_train)

    # Evaluate on validation set
    with torch.no_grad():
        model.eval()
        val_inputs = Variable(torch.FloatTensor(X_val.values))
        val_labels = Variable(torch.LongTensor(y_val.values))
        val_outputs = model(val_inputs)
        val_loss_value = loss_func(val_outputs, val_labels)
        val_acc_value = get_accuracy(val_outputs, val_labels, len(X_val))
        val_loss.append(val_loss_value)
        val_acc.append(val_acc_value)

    # Train on training set
    model.train()
    train_batch_loss = []
    train_batch_acc = []
    for i in range(batch_no):
        start = i * batch_size
        end = start + batch_size
        inputs = Variable(torch.FloatTensor(X_train.values[start:end]))
        labels = Variable(torch.LongTensor(y_train.values[start:end]))

        optimizer.zero_grad()

        # forward -> backward -> optimize
        outputs = model(inputs)
        loss = loss_func(outputs, labels)
        loss.backward()
        optimizer.step()

        train_batch_loss.append(loss.item())
        acc = get_accuracy(outputs, labels, batch_size)
        train_batch_acc.append(acc)

    train_loss_value = sum(train_batch_loss) / len(train_batch_loss)
    train_acc_value = sum(train_batch_acc) / len(train_batch_acc)
    train_loss.append(train_loss_value)
    train_acc.append(train_acc_value)

    print(f"Epochs: {epoch+1}, Train Loss: {train_loss_value:.4f}, Train Acc: {train_acc_value:.4f}, Val Loss: {val_loss_value:.4f}, Val Acc: {val_acc_value:.4f}")

# plot train and val loss
plt.plot(train_loss, label="Train Loss")
plt.plot(val_loss, label="Val Loss")
plt.legend()
plt.title("Training and Validation Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.show()

# plot train and val accuracy
plt.plot(train_acc, label="Train Acc")
plt.plot(val_acc, label="Val Acc")
plt.legend()
plt.title("Training and Validation Accuracy")
plt.xlabel("Epochs")
plt.ylabel("Accuracy")
plt.ylim([0, 20.0])  # set y-axis limits
plt.xlim([0, num_epochs])  # set x-axis limits
plt.show()

# Evaluate on test set
with torch.no_grad():
    model.eval()
    test_inputs = Variable(torch.FloatTensor(X_test.values))
    test_labels = Variable(torch.LongTensor(y_test.values))
    test_outputs = model(test_inputs)
    test_acc = get_accuracy(test_outputs, test_labels, len(X_test))
    print(f"Test Acc: {test_acc}")

