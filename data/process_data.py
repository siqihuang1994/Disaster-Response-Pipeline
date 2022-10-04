import sys
import pandas as pd
from sqlalchemy import create_engine

def load_data(messages_filepath, categories_filepath):
    """
    load_data
    Load data from csv files and merge to a single pandas dataframe
    
    Input:
    messages_filepath       filepath to messages csv file
    categories_filepath     filepath to categories csv file
    
    Returns:
    df      dataframe merging categories and messages
    
    """    
    messages = pd.read_csv(messages_filepath)
    categories = pd.read_csv(categories_filepath)
    df = messages.merge(categories, how='inner', on='id')
    
    return df


def clean_data(df):
    """
    clean_data
    Create a dataframe replacing original categories column with the 36 individual category columns and rename the columns 
    Drop non-binary records and duplicates
    
    Input: 
    df      merged dataframe contains info from categories and messages
    
    Returns:
    df      cleaned version of input dataframe
    """
    
    # create a dataframe of the 36 individual category columns
    categories = df['categories'].str.split(";",expand=True)
    # select the first row of the categories dataframe
    row = categories[:1]

    # use this row to extract a list of new column names for categoties
    category_colnames = row.apply(lambda x:x.str.slice(0,len(x)-3)).iloc[0]
    # rename the columns of `categories`
    categories.columns = category_colnames
    
    # Convert category values to just numbers 0 or 1
    for column in categories:
    # set each value to be the last character of the string
        categories[column] = categories[column].astype(str).str[-1:]
    
    # convert column from string to numeric
        categories[column] = pd.to_numeric(categories[column])
    
    # concatenate the original dataframe with the new `categories` dataframe
    df=df.drop('categories',axis=1)
    df = pd.concat([df, categories], axis=1)
    
    # drop non-binary records
    df.drop(df[df['age'] < 30.0].index, inplace=True)
    
    # drop duplicates
    df=df.drop_duplicates()
    
    return df
    
    


def save_data(df, database_filename):
    """
    save_data
    Save the data to database
    
    Input:
    df                  dataframe to be saved
    database_filename   the database name to which the dataframe is to be saved
    """
    
    engine = create_engine("sqlite:///"+ database_filename)
    df.to_sql('messages', engine, index=False, if_exists='replace')  


def main():
    if len(sys.argv) == 4:

        messages_filepath, categories_filepath, database_filepath = sys.argv[1:]

        print('Loading data...\n    MESSAGES: {}\n    CATEGORIES: {}'
              .format(messages_filepath, categories_filepath))
        df = load_data(messages_filepath, categories_filepath)

        print('Cleaning data...')
        df = clean_data(df)
        
        print('Saving data...\n    DATABASE: {}'.format(database_filepath))
        save_data(df, database_filepath)
        
        print('Cleaned data saved to database!')
    
    else:
        print('Please provide the filepaths of the messages and categories '\
              'datasets as the first and second argument respectively, as '\
              'well as the filepath of the database to save the cleaned data '\
              'to as the third argument. \n\nExample: python process_data.py '\
              'disaster_messages.csv disaster_categories.csv '\
              'DisasterResponse.db')


if __name__ == '__main__':
    main()
