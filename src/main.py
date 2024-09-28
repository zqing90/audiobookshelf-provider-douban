
from fastapi import FastAPI

from douban import DoubanBookSearcher

app = FastAPI()


@app.get("/search")
async def search(query:str=None,auther:str=None):
    books=[]
    if str is not None and str != "":
        book_search = DoubanBookSearcher()
        books = book_search.search_books(query)
    return books

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
