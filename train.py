from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import Adam
import numpy as np
from scipy.sparse import hstack
import sys
import time

from utils import *

seed = 182
np.random.seed(seed)

adj, features, y_train, y_val, y_test, train_mask, val_mask, test_mask = load_data("cora")

# Write adjancency matrix to file.
f = open("adj.txt", "w+")
it = np.nditer(adj.todense(), flags=['multi_index'])
save_stdout = sys.stdout
sys.stdout = open('trash', 'w')
while not it.finished:
  if it[0]:
    f.write("%s,%s,%.1f\n" % (it.multi_index[0]+1, it.multi_index[1]+1, it[0]))
  it.iternext()
sys.stdout = save_stdout
f.close()

# Write train labels to file.
f = open("train_labels.txt", "w+")
for i in np.where(train_mask)[0]:
  f.write("%s %s\n" % (i+1, np.where(y_train[i])[0][0]+1))
f.close()

a = np.arange(6).reshape(2,3)
it = np.nditer(a, flags=['multi_index'])
while not it.finished:
    print("%d <%d>" % (it[0], it.index),)
    it.iternext()

features = preprocess_features(features)
support = preprocess_adj(adj)

# features_linear = support.dot(features)
# features_quad = support.dot(features_linear)
# features = hstack([features_linear, features_quad])

features = support.dot(support.dot(features))

features = features.todense()

model = Sequential()
model.add(Dropout(0.5))
model.add(Dense(
  units=y_train.shape[1],
  input_dim=features.shape[1],
  activation='softmax'))

model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.1), metrics=['accuracy'])

# Helper variables for main training loop
wait = 0
preds = None
best_val_loss = 99999

# Fit
EPOCHS = 250
PATIENCE = 10
for epoch in range(1, EPOCHS+1):
  t = time.time()
  model.fit(features, y_train, sample_weight=train_mask, epochs=1, batch_size=adj.shape[0], shuffle=False, verbose=False)
  preds = model.predict(features, batch_size=adj.shape[0])
  train_val_loss, train_val_acc = evaluate_preds(preds, [y_train, y_val],
                           [train_mask, val_mask])
  print("Epoch: {:04d}".format(epoch),
      "train_loss= {:.4f}".format(train_val_loss[0]),
      "train_acc= {:.4f}".format(train_val_acc[0]),
      "val_loss= {:.4f}".format(train_val_loss[1]),
      "val_acc= {:.4f}".format(train_val_acc[1]),
      "time= {:.4f}".format(time.time() - t))
  # Early stopping
  if train_val_loss[1] < best_val_loss:
    best_val_loss = train_val_loss[1]
    wait = 0
  else:
    if wait >= PATIENCE:
      print('Epoch {}: early stopping'.format(epoch))
      break
    wait += 1

scores = model.evaluate(features[train_mask, :], y_train[train_mask, :])
print("\n%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))

scores = model.evaluate(features[val_mask, :], y_val[val_mask, :])
print("\n%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))

scores = model.evaluate(features[test_mask, :], y_test[test_mask, :])
print("\n%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))