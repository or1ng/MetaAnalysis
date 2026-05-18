from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import get_db
from models.user import User
from schemas.auth import RegisterRequest, LoginRequest, RefreshRequest, TokenOut, UserOut
from utils.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from utils.response import ApiResponse

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        return ApiResponse.fail(message="用户名已存在", code=400)

    # 创建用户
    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # 生成Token
    token_data = {"user_id": user.id, "username": user.username}
    return ApiResponse.ok(data={
        "user_id": user.id,
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
    })


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        return ApiResponse.fail(message="用户名或密码错误", code=401)

    if user.status == "disabled":
        return ApiResponse.fail(message="账号已禁用", code=403)

    token_data = {"user_id": user.id, "username": user.username, "role": user.role}
    return ApiResponse.ok(data={
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "user_id": user.id,
        "username": user.username,
    })


@router.post("/refresh")
async def refresh_token(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        return ApiResponse.fail(message="刷新令牌无效", code=401)
    token_data = {"user_id": payload["user_id"], "username": payload["username"]}
    return ApiResponse.ok(data={
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
    })


@router.get("/me")
async def get_current_user(db: AsyncSession = Depends(get_db)):
    """获取当前用户信息 - 需要Token，暂时简化处理"""
    return ApiResponse.ok(data={"message": "请携带Token访问此接口"})
