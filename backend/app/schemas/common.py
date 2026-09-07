"""统一响应包装（全项目唯一响应契约，见 rules/06）。

- 成功：{code: 0, message: "ok", data: ...}
- 分页：data 为 {total, page, page_size, items}
- 业务失败：HTTP 200 + code != 0 + 人类可读 message
"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None


class PageData(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    items: list[T]


def ok(data: object = None, message: str = "ok") -> ApiResponse:
    return ApiResponse(code=0, message=message, data=data)


def fail(code: int, message: str) -> ApiResponse:
    return ApiResponse(code=code, message=message, data=None)
