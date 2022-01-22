import pandas as pd
import string


def motech():
	df = pd.read_csv('dataset.csv')
	df = df[['CATEGORY', 'BOOK']]
	print(df['BOOK'].head(5))
	df.columns = ['CATEGORY', 'BOOK']
	df.BOOK = df.BOOK.apply(lambda x: x.lower())
	df.BOOK = df.BOOK.apply(lambda x: x.translate(str.maketrans('','',string.punctuation)))
	df.BOOK = df.BOOK.apply(lambda x: x.translate(str.maketrans('','','1234567890')))
	df['category_id'] = df['CATEGORY'].factorize()[0]

	return df