from collections import Counter
from keras.models import Sequential
from keras import layers
from keras.utils import pad_sequences
from keras.preprocessing.text import Tokenizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from math import sqrt
from sklearn.metrics import accuracy_score
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

MAX_SEQUENCE_LENGTH = 5000
MAX_NUM_WORDS = 25000
EMBEDDING_DIM = 300
TEST_SPLIT = 0.2


class TextClassifier:
    def __init__(self, max_sequence_length, max_num_words, embedding_dim, test_split):
        self.max_sequence_length = max_sequence_length
        self.max_num_words = max_num_words
        self.embedding_dim = embedding_dim
        self.test_split = test_split
        self.text_data = 'https://raw.githubusercontent.com/codesapienbe/fake-news/master/data/fake_or_real_news.csv'
        self.df = None
        self.texts = None
        self.labels = None
        self.tokenizer = None
        self.word_index = None
        self.data = None
        self.labels = None
        self.x_train = None
        self.x_val = None
        self.y_train = None
        self.y_val = None
        self.model = None
        self.history = None

    def read_data(self):
        self.df = pd.read_csv(self.text_data)
        self.df.drop(labels=['id', 'title'], axis='columns', inplace=True)
        mask = list(self.df['text'].apply(lambda x: len(x) > 0))
        self.df = self.df[mask]
        self.texts = self.df['text']
        self.labels = self.df['label']
        print('Found %s texts.' % self.texts.shape[0])

    def plot_text_lengths(self):
        text_lengths = self.texts.apply(lambda x: len(x.split(" ")))
        plt.hist(text_lengths)
        plt.show()

    def prepare_data(self):
        vectorizer = CountVectorizer(
            analyzer="word",
            binary=True,
            min_df=2,
            stop_words='english'
        )
        docarray = vectorizer.fit_transform(self.texts).toarray()
        self.docterm = pd.DataFrame(
            docarray, columns=vectorizer.get_feature_names_out())
        self.docterm_train, self.docterm_test, self.y_train, self.y_test = train_test_split(
            self.docterm, self.labels, test_size=self.test_split
        )

    def train_naive_bayes_model(self):
        self.model = MultinomialNB()
        self.model.fit(self.docterm_train, self.y_train)

    def evaluate_model(self):
        train_acc, test_acc = self._calculate_accuracy(
            self.model.predict, self.docterm_train, self.y_train, self.docterm_test, self.y_test
        )
        print("Training Accuracy: {:.2f}%".format(train_acc * 100))
        print("Testing Accuracy: {:.2f}%".format(test_acc * 100))
        n = self.docterm_test.shape[0]
        lb, ub = self._calculate_error_confidence(1 - test_acc, n)
        print(
            "95% confidence interval: {:.2f}%-{:.2f}%".format((1 - ub) * 100, (1 - lb) * 100))

    def _calculate_accuracy(self, predict_fun, X_train, y_train, X_test, y_test):
        y_predict_train = predict_fun(X_train)
        train_acc = accuracy_score(y_train, y_predict_train)
        y_predict_test = predict_fun(X_test)
        test_acc = accuracy_score(y_test, y_predict_test)
        return train_acc, test_acc

    def _calculate_error_confidence(self, error, n):
        term = 1.96 * sqrt((error * (1 - error)) / n)
        lb = error - term
        ub = error + term
        return lb, ub

    def vectorize_text_samples(self):
        self.tokenizer = Tokenizer(num_words=self.max_num_words)
        self.tokenizer.fit_on_texts(self.texts)
        sequences = self.tokenizer.texts_to_sequences(self.texts)
        self.word_index = self.tokenizer.word_index
        num_words = min(self.max_num_words, len(self.word_index)) + 1
        self.data = pad_sequences(
            sequences,
            maxlen=self.max_sequence_length,
            padding='pre',
            truncating='pre'
        )
        print('Found %s unique tokens.' % len(self.word_index))
        print('Shape of data tensor:', self.data.shape)
        print('Shape of label tensor:', self.labels.shape)

    def split_data(self):
        self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(
            self.data,
            self.labels.apply(lambda x: 0 if x == 'FAKE' else 1),
            test_size=self.test_split
        )

    def build_model(self):
        self.model = Sequential(
            [
                layers.Embedding(
                    self.max_num_words,
                    self.embedding_dim,
                    input_length=self.max_sequence_length,
                    trainable=True
                ),
                layers.Conv1D(128, 5, activation='relu'),
                layers.GlobalMaxPooling1D(),
                layers.Dense(128, activation='relu'),
                layers.Dense(1, activation='sigmoid')
            ]
        )
        self.model.compile(
            loss='binary_crossentropy',
            optimizer='rmsprop',
            metrics=['accuracy']
        )
        self.model.summary()

    def train_model(self):
        self.history = self.model.fit(
            self.x_train,
            self.y_train,
            batch_size=128,
            epochs=10,
            validation_data=(self.x_val, self.y_val)
        )

    def plot_accuracy(self):
        plt.plot(self.history.history['accuracy'])
        plt.plot(self.history.history['val_accuracy'])
        plt.title('Model accuracy')
        plt.ylabel('Accuracy')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Test'], loc='upper left')
        plt.show()

    def evaluate_cnn_model(self):
        train_acc, test_acc = self._calculate_accuracy(
            lambda x: np.rint(self.model.predict(
                x)), self.x_train, self.y_train, self.x_val, self.y_val
        )
        print("Training Accuracy: {:.2f}%".format(train_acc * 100))
        print("Testing Accuracy: {:.2f}%".format(test_acc * 100))
        n = self.x_val.shape[0]
        lb, ub = self._calculate_error_confidence(1 - test_acc, n)
        print(
            "95% confidence interval: {:.2f}%-{:.2f}%".format((1 - ub) * 100, (1 - lb) * 100))

    def print_common_words(self):
        counter = Counter(self.tokenizer.word_counts)
        print(counter.most_common(20))

    def save_model(self, filename):
        self.model.save(filename)


# Create an instance of the TextClassifier
classifier = TextClassifier(
    MAX_SEQUENCE_LENGTH,
    MAX_NUM_WORDS,
    EMBEDDING_DIM,
    TEST_SPLIT
)

# Perform text classification steps
classifier.read_data()
classifier.plot_text_lengths

classifier.prepare_data()
classifier.train_naive_bayes_model()
classifier.evaluate_model()
classifier.vectorize_text_samples()

classifier.split_data()
classifier.build_model()
classifier.train_model()

classifier.plot_accuracy()
classifier.evaluate_cnn_model()
classifier.print_common_words()

classifier.save_model('model.h5')


# Make sure to import the required libraries and define the constant variables (`MAX_SEQUENCE_LENGTH`, `MAX_NUM_WORDS`, `EMBEDDING_DIM`, `TEST_SPLIT`) before running the code.
