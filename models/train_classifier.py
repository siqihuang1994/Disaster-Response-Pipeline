import sys
import nltk
nltk.download(['punkt', 'wordnet','averaged_perceptron_tagger'])

# import libraries
import re
import numpy as np
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

from sqlalchemy import create_engine
import pickle

class StartingVerbExtractor(BaseEstimator, TransformerMixin):

    def starting_verb(self, text):
        sentence_list = nltk.sent_tokenize(text)
        for sentence in sentence_list:
            pos_tags = nltk.pos_tag(tokenize(sentence))
            first_word, first_tag = pos_tags[0]
            if first_tag in ['VB', 'VBP'] or first_word == 'RT':
                return True
        return False

    def fit(self, x, y=None):
        return self

    def transform(self, X):
        X_tagged = pd.Series(X).apply(self.starting_verb)
        return pd.DataFrame(X_tagged)
    
    
def load_data(database_filepath):
    """
    load_data
    Load data from database
    
    Input:
    database_filepath       filepath to the database where dataframe is stored
    
    Returns:
    X               dataframe contains explantory variables
    Y               dataframe contains the response variable
    category_names  list of category names
    """
    
    engine = create_engine("sqlite:///" + database_filepath)
    df = pd.read_sql_table('messages', engine)
    X = df['message'].values
    Y = df.iloc[:, 4:].values
    category_names = df.iloc[:, 4:].columns
    
    return X, Y, category_names

def tokenize(text):
    """
    tokenize
    tokenize, lemmatize and clean a text
    
    Input:
    text      text need to be tokenized, lemmatized and cleaned
    
    Returns:
    clean_tokens    A list of tokenized, lemmatized and cleaned text
    """
        
    url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    detected_urls = re.findall(url_regex, text)
    for url in detected_urls:
        text = text.replace(url, "urlplaceholder")

    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()

    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)

    return clean_tokens


def build_model():
    """
    build_model
    Process cleaned text and model pipeline
    Define parameters for GridSearchCV
    
    Returns:
    cv      gridsearch object as final model pipeline
    """
    
    pipeline = Pipeline([
        ('features', FeatureUnion([

            ('text_pipeline', Pipeline([
                ('vect', CountVectorizer(tokenizer=tokenize)),
                ('tfidf', TfidfTransformer())
            ])),

            ('starting_verb', StartingVerbExtractor())
        ])),

        ('clf', MultiOutputClassifier(RandomForestClassifier()))
    ])
    
    
    parameters = {
            'features__text_pipeline__vect__ngram_range': ((1, 1), (1, 2)),
            'clf__estimator__n_estimators': [20, 50, 100],
            'clf__estimator__min_samples_split': [2,5,10]
        }

    cv = GridSearchCV(pipeline, param_grid=parameters)
    
    return cv


def evaluate_model(model, X_test, Y_test, category_names):
    """
    evaluate_model
    Evaluate the models with different parameters and determine the best one 
    
    Input:
    model               the final model built
    X_test              dataframe contains test data for explantory variables
    Y_test              dataframe contains test data for the response variable
    category_names      list of category names 
    
    Returns:
    best_model      the final model that fits the data best
    """
    result = model.fit(X_test, Y_test)
    best_model = result.best_estimator_
    Y_pred = best_model.predict(X_test)
    
    y_test=pd.DataFrame(Y_test)
    y_pred=pd.DataFrame(Y_pred)
    y_test.columns = category_names
    y_pred.columns = category_names

    for column in category_names:
        print(classification_report(y_test[column], y_pred[column]))
        accuracy = (y_test[column] == y_pred[column]).mean()
        print("Accuracy:", accuracy)
        
    return best_model

def save_model(model, model_filepath):
    """
    save_model
    Save the final model to the desired location
    
    Input:
    model               the final model built
    model_filepath      filepath to save the model
    """
    
    pickle.dump(model, open(model_filepath, 'wb'))
    
    
def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        best_model=evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(best_model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()
