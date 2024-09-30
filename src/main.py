
import os
from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import requests

from douban import DoubanBookSearcher

app = FastAPI()

# 获取当前工作目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 指定静态文件夹的路径
static_folder_path = os.path.join(base_dir, "tmp")



#静态目录
app.mount("/tmp", StaticFiles(directory=static_folder_path), name="tmp")

@app.get("/search")
async def search(request:FastAPIRequest,query:str=None,auther:str=None):
    books=[]
    local_base_url = f"{request.url.scheme}://{request.url.hostname}:{request.url.port}"
    proxy_url =f"{local_base_url}/proxy-image/"
    print(local_base_url)
    if str is not None and str != "":
        book_search = DoubanBookSearcher()
        # 直接使用豆瓣的地址
        # books = book_search.search_books(query)
        # 图片代理转换地址
        books = book_search.search_books(query,proxy_url=proxy_url)
        # 本地下载后提供静态地址
        # books = book_search.search_books(query,local_base_url)
    return books

@app.get("/list_tmp_files", response_class=HTMLResponse)
async def list_static_files():
    """列出静态文件
    """
    # 确保静态文件夹存在
    if not os.path.exists(static_folder_path):
        raise HTTPException(status_code=404, detail="Static directory not found")

    # 获取目录中的所有文件和子目录
    files = os.listdir(static_folder_path)

    # 构建 HTML 响应
    html_content = """
    <html>
    <head>
        <title>Static Files</title>
    </head>
    <body>
        <h1>Static Files</h1>
        <ul>
    """

    for file in files:
        file_path = f"/tmp/{file}"
        html_content += f'<li><a href="{file_path}">{file}</a></li>'

    html_content += """
        </ul>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content, status_code=200)

@app.get("/proxy-image/{url:path}")
async def proxy_image(url: str):
    if url == "":
        return {"error":"proxy url is blank"}
    # 发送 GET 请求到提供的 URL
    response = requests.get(url, stream=True)
    
    # 检查响应状态码是否为200 (OK)
    if response.status_code == 200:
        # 获取图片的内容类型
        content_type = response.headers.get('content-type', 'application/octet-stream')
        
        # 使用StreamingResponse返回图片内容
        return StreamingResponse(
            response.iter_content(chunk_size=1024),
            media_type=content_type,
            headers = {
                "Content-Disposition": f"inline; filename=image.{content_type.split('/')[-1]}",
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3573.0 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://book.douban.com/'
                }

        )
    else:
        # 如果图片无法获取，则抛出异常
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch image")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
