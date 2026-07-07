"""FastAPI 演示 — 包含两个端点的最小 Web API。"""

from fastapi import FastAPI, Response

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """get不带参数测试"""
    return {"Hello": "World"}


@app.get("/users/{user_id}")
def read_user(user_id: int, q: str | None = None) -> dict[str, int | str | None]:
    """get带参数请求测试"""
    return {"item_id": user_id, "q": q}


@app.post("/")
def read_post(response: Response) -> dict[str, int | str | None] :
    """post请求测试"""

    return {"message": "POST received"}

@app.head("/")
def read_head() -> Response:
    """head请求测试"""
    return Response(
        content="",
        headers={"X-Resource-Exists": "" , "Content-Length": "1024"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)