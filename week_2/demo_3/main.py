"""FastAPI 演示 — 包含两个端点的最小 Web API。"""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """根端点，返回问候语。"""
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None) -> dict[str, int | str | None]:
    """按 ID 获取条目，支持可选的查询参数。"""
    return {"item_id": item_id, "q": q}
