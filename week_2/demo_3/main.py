"""FastAPI 演示 — 包含两个端点的最小 Web API。"""

from fastapi import FastAPI, Response

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """根端点，返回问候语。"""
    return {"Hello": "World"}


@app.get("/users/{user_id}")
def read_user(user_id: int, q: str | None = None) -> dict[str, int | str | None]:
    """按 ID 获取条目，支持可选的查询参数。"""
    return {"item_id": user_id, "q": q}


@app.post("/")
def read_post(response: Response) -> dict[str, int | str | None] :
    """"""

    return {"message": "POST received"}

@app.head("/")
def read_head() -> Response:
    """"""
    return Response(
        content="",
        headers={"X-Resource-Exists": "" , "Content-Length": "1024"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)