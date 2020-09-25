### Reading List Database Project
### Using Goodreads API as library database

import os.path
from os import path
import http.client
import mimetypes
import csv
import xmltodict
import json
from datetime import datetime

### Function Definitions ###
def saveFile( filename, fields, rows ):
    with open(filename, "w", newline = '') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerows(rows)

def formatMyRawDate(dateStringToFormat):
    if dateStringToFormat is None:
        myNewDate = None
    else:
        datefieldobject = datetime.strptime(dateStringToFormat, '%a %b %d %H:%M:%S %z %Y')
        myNewDate = datefieldobject.date()

## for later feature: create new function to get a discrete rating based on the avg rating


### Bookshelf Loading: Get current files or create new ones

### GoodreadsAPI -- Get books by member shelf given a list of shelf names
if path.exists('books.csv'):
    
    with open('books.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

    for row in csv_reader:
        current_books_rows.append(row[0])
    
    print(len(current_books_rows))

### Since no files were found, build them here based on member ID 
else:
    ## can be set to run on any Goodreads member ID
    # myMemberID = input(['Enter Goodreads Member ID'])
    myMemberID = 727455
    print(myMemberID)

    ## initialize book and author tables
    books_filename = 'books.csv'
    books_rows = []
    books_fields = [
      'id',
      'isbn',
      'isbn13',
      'title',
      'num_pages',
      'partOf_series',
      'series_id',
      'publisher',
      'publication_year',
      'avg_rating',
      'ratings_cnt',
      'author_id',
      'date_added',
      'start_date',
      'finish_date',
      'myRating',
      'myReview',
      'readStatus'
    ]

    authors_filename = 'authors.csv'
    authors_rows = []
    authors_fields = [
        'id',
        'name',
        'avg_rating',
        'ratings_cnt'
    ]
 

    ## initialize paging variables (assume there is at least 1 book on the shelf to get)
    reviewlist = []
    pageStart = 1
    booksData = 0
    totalBooksOnShelf = 1   
    
    while booksData < totalBooksOnShelf:
        print('pageStart: ' + str(pageStart))
        booksData_at_start = booksData
        per_page = 100
        
        conn = http.client.HTTPSConnection('www.goodreads.com')
        payload = ''
        headers = {
            'Cookie': 'ccsid=355-8086303-7158046; locale=en'
        }
        uri = '/review/list?v=2&id=' + str(myMemberID) + '&key=kNP4OTpBRIGzIuvPFFTCQ&page=' + str(pageStart) + '&per_page=' + str(per_page)

        conn.request('GET', uri, payload, headers)
        res = conn.getresponse()
        data = res.read()
        
        returnObject = xmltodict.parse(data.decode('utf-8'))
        GoodreadsResponse = returnObject.get('GoodreadsResponse')
        reviewsReturned = GoodreadsResponse.get('reviews')
        book_start_num = int(reviewsReturned.get('@start'))
        book_end_num = int(reviewsReturned.get('@end'))
        totalBooksOnShelf = int(reviewsReturned.get('@total'))
        
        thisReviewlist = reviewsReturned.get('review')
        reviewlist.extend(thisReviewlist)
        booksData += book_end_num
        pageStart += 1
        print('totalBooksOnShelf: '+ str(totalBooksOnShelf))
        print('booksDataThisPage: ' + str(booksData - booksData_at_start))
    
    for review in reviewlist:
        
        ## parse book data
        book = review.get('book')
        book_id = review.get('id')
        isbn = book.get('isbn')
        if isinstance(isbn, dict):
            isbn = None
        isbn13 = book.get('isbn13')
        if isinstance(isbn13, dict):
            isbn13 = None
        title = book.get('title')
        num_pages_raw = book.get('num_pages')
        if num_pages_raw is None:
            num_pages = None
        else:
            num_pages = int(num_pages_raw)
        publisher = book.get('publisher')
        publication_year = book.get('published')
        book_avg_rating = book.get('average_rating')
        book_ratings_cnt = book.get('ratings_count')
        
        date_added_str = review.get('date_added')
        # date_added = formatMyRawDate(review.get('date_added'))
        if date_added_str is None:
            date_added = None
        else:
            datefieldobject = datetime.strptime(date_added_str, '%a %b %d %H:%M:%S %z %Y')
            date_added = datefieldobject.date()
            
        start_date_str = review.get('started_at')
        if start_date_str is None:
            start_date = None
        else:
            datefieldobject = datetime.strptime(start_date_str, '%a %b %d %H:%M:%S %z %Y')
            start_date = datefieldobject.date()
        
        finish_date_str = review.get('read_at')
        if finish_date_str is None:
            finish_date = None
        else:
            datefieldobject = datetime.strptime(finish_date_str, '%a %b %d %H:%M:%S %z %Y')
            finish_date = datefieldobject.date()

        myRating = review.get('rating')
        myReview = review.get('body')
        
        shelves = review.get('shelves')
        shelf = shelves.get('shelf')
        shelfName = shelf.get('@name')
        
        ## parse author data
        authors = book.get('authors')
        for author in authors:
            singleAuthor = authors.get('author')
            author_id = singleAuthor.get('id')
            author_name = singleAuthor.get('name')
            author_avg_rating = singleAuthor.get('average_rating')
            author_ratings_cnt = singleAuthor.get('ratings_count')
        
        bookRow = [ 
            book_id, 
            isbn, 
            isbn13, 
            title, 
            num_pages, 
            "", 
            "", 
            publisher, 
            publication_year, 
            book_avg_rating, 
            book_ratings_cnt, 
            author_id, 
            date_added, 
            start_date, 
            finish_date, 
            myRating, 
            myReview, 
            shelfName
            ]
        books_rows.append(bookRow)
        
        authorRow = [ author_id, author_name, author_avg_rating, author_ratings_cnt ]
        if authorRow not in authors_rows:
            authors_rows.append(authorRow)

    saveFile(books_filename, books_fields, books_rows)
    saveFile(authors_filename, authors_fields, authors_rows)
    
print('book shelf loading complete')


### Goodreads API -- Get genre for each book using ISBN

# print('loading genres for '+ str(len(books_rows)) +' books')
# genres_filename = 'genres.csv'
# genres_rows = []
# genres_fields = [
    # 'id',
    # 'book_id',
    # 'isbn',
    # 'isFiction',
    # 'all_genres',
    # 'filtered_genres',
    # 'top_genre'
    # ]
# genre_id = 1

## Common shelf names on Goodreads that are not valid genres
# genreExceptions = [
# 'to-read', 'currently-reading', 'owned', 'default', 'favorites', 'books-i-own',
# 'ebook', 'kindle', 'library', 'audiobook', 'owned-books', 'audiobooks', 'my-books',
# 'ebooks', 'to-buy', 'english', 'calibre', 'books', 'british', 'audio', 'my-library',
# 'favourites', 're-read', 'general', 'e-books', 'fiction', 'nonfiction', 'non-fiction'
# ]

# for eachbook in books_rows: 
    
    # book_id = eachbook[0]
    # isbn = eachbook[1]
    # all_genres = []
    # filtered_genres = []
    # print(genre_id)

    # if isbn is not None:
        # conn = http.client.HTTPSConnection("www.goodreads.com")
        # payload = ''
        # headers = {
            # 'Cookie': 'ccsid=355-8086303-7158046; locale=en; BCSI-CS-8bdb7bc5f1ba9573=1'
        # }
        # uri = "/book/isbn/"+ isbn +"?format=xml&key=kNP4OTpBRIGzIuvPFFTCQ&isbn="+ isbn
        # conn.request("GET", uri, payload, headers)
        # res = conn.getresponse()
        # data = res.read()
        
        # returnObject = xmltodict.parse(data.decode('utf-8'))
        # GoodreadsResponse = returnObject.get('GoodreadsResponse')
        # book = GoodreadsResponse.get('book')
        # popularShelves = book.get('popular_shelves')
        # shelfName = popularShelves.get('shelf')

        # for i in shelfName:
            # genre_name = i.get('@name')
            # all_genres.append(genre_name)
             
            # if genre_name not in genreExceptions:
                # filtered_genres.append(genre_name)
            
            # if "fiction" in genre_name:
                # if "non" in genre_name:
                    # fiction_status = False
                # else:
                    # fiction_status = True
        # thisRow = [ genre_id, book_id, isbn, fiction_status, all_genres, filtered_genres, filtered_genres[0]]
    # else:
        # thisRow = [ genre_id, book_id, isbn, None, None, None, None]
    
    # genres_rows.append(thisRow)    
    # genre_id += 1

# with open(genres_filename, "w", newline = '', encoding="utf-8") as csvfile:
        # csvwriter = csv.writer(csvfile)
        # csvwriter.writerow(genres_fields)
        # csvwriter.writerows(genres_rows)

# print('genre data complete')