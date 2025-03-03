from collections import defaultdict
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.models import Model
import pickle


class concat_model:
    def __init__(self, feature_len, feature_name, dout):
        self.feature_len = feature_len
        self.feature_name = feature_name
        self.model = None
        self.dout = dout

    def make_model(self):
        layer_dict = defaultdict()
        for L_in, name in zip(self.feature_len, self.feature_name):
            layer_dict[name] = defaultdict()
            layer_dict[name]['input'] = layers.Input(shape=(L_in,), name='input_' + name)
        concat_layer = layers.concatenate([layer_dict[fea]['input'] for fea in self.feature_name], name='concat')

        # classifier = layers.Dense(128, activation='relu', name='dense1_classifier')(concat_layer)
        # classifier = layers.BatchNormalization()(classifier)
        # classifier = layers.Dense(8, activation='relu', name='dense7_classifier')(classifier)
        # classifier = layers.BatchNormalization()(classifier)
        # classifier = layers.Dense(1, activation='sigmoid', name='out_classifier')(classifier)

        N_feature = sum(self.feature_len)
        classifier = layers.Dropout(self.dout, input_shape=(N_feature,), name='drop1_classifier')(concat_layer)
        classifier = layers.Dense(128, activation='sigmoid', name='dense1_classifier')(classifier)
        classifier = layers.Dropout(self.dout, name='drop2_classifier')(classifier)
        classifier = layers.Dense(128, activation='tanh', name='dense2_classifier')(classifier)
        classifier = layers.Dropout(self.dout, name='drop3_classifier')(classifier)
        classifier = layers.Dense(32, activation='tanh', name='dense3_classifier')(classifier)
        classifier = layers.Dropout(self.dout, name='drop4_classifier')(classifier)
        classifier = layers.Dense(32, activation='tanh', name='dense4_classifier')(classifier)
        classifier = layers.Dropout(self.dout, name='drop5_classifier')(classifier)
        classifier = layers.Dense(16, activation='tanh', name='dense5_classifier')(classifier)
        classifier = layers.Dropout(self.dout, name='drop6_classifier')(classifier)
        classifier = layers.Dense(16, activation='tanh', name='dense6_classifier')(classifier)
        classifier = layers.Dense(8, activation='tanh', name='dense7_classifier')(classifier)
        classifier = layers.Dense(1, activation='sigmoid', name='out_classifier')(classifier)

        self.model = Model([layer_dict[fea]['input'] for fea in self.feature_name], classifier)

        self.model.compile(loss='binary_crossentropy',
                           optimizer='adam',
                           metrics=['accuracy', tf.keras.metrics.AUC()])

    def train_model(self, train_data, validation_data, checkpoint_filepath, Epochs=10,
                    batch_size=64, weighted_sample=True):

        if weighted_sample:
            sample_weight = np.where(train_data['label'] == 1, len(train_data['label'][train_data['label'] == 0])
                                     / len(train_data['label'][train_data['label'] == 1]), 1)
        else:
            sample_weight = np.ones_like(train_data['label'])

        model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
            filepath=checkpoint_filepath,
            save_weights_only=True,
            monitor='val_auc',
            mode='max',
            save_best_only=True)

        early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_auc', patience=30, mode='max')

        self.model.fit([train_data[fe] for fe in self.feature_name], train_data['label'],
                       validation_data=([validation_data[fe] for fe in self.feature_name], validation_data['label']),
                       batch_size=batch_size,
                       sample_weight=sample_weight,
                       epochs=Epochs,
                       callbacks=[model_checkpoint_callback, early_stop],
                       verbose=2)

        self.model.load_weights(checkpoint_filepath)

        self.model.evaluate([validation_data[fe] for fe in self.feature_name], validation_data['label'],
                            verbose=2)
