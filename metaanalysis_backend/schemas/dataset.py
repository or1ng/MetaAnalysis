from pydantic import BaseModel


class ColumnMeta(BaseModel):
    name: str
    type: str
    missing_rate: float = 0.0


class DatasetOut(BaseModel):
    id: int
    name: str
    file_type: str
    file_size: int
    row_count: int
    col_count: int
    columns_json: list = []
    is_cleaned: int
    version: int
    status: str
    created_at: str

    class Config:
        from_attributes = True


class DatasetRename(BaseModel):
    name: str
