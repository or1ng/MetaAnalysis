from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models import get_db
from utils.response import ApiResponse

router = APIRouter(prefix="/api/user", tags=["用户中心"])


@router.get("/profile")
async def get_profile(db: AsyncSession = Depends(get_db)):
    """获取个人信息"""
    # TODO: 步骤8实现用户中心
    return ApiResponse.ok(data={
        "username": "demo",
        "email": "demo@metaanalysis.com",
        "role": "free",
        "storage_used": 0,
        "storage_limit": 536870912,
    })


@router.put("/profile")
async def update_profile(db: AsyncSession = Depends(get_db)):
    """更新个人信息"""
    return ApiResponse.ok(message="开发中")


@router.put("/password")
async def change_password(db: AsyncSession = Depends(get_db)):
    """修改密码"""
    return ApiResponse.ok(message="开发中")


@router.get("/storage")
async def get_storage(db: AsyncSession = Depends(get_db)):
    """存储用量"""
    return ApiResponse.ok(data={"used": 0, "limit": 536870912, "usage_percent": 0})
