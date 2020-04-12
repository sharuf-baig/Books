import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
	f = open('books.csv')
	reader = csv.reader(f)

	for isbn,title,author,year in reader:
		db.execute("INSERT INTO books(isbn,title,author,year) VALUES (:isbn,:title,:author,:year)",{"isbn":isbn,"title":title,"author":author,"year":year})
		print(f"{isbn} {title} {author} {year} added")
	db.commit()    
if __name__=="__main__":
	main()