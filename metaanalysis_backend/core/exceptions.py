from utils.response import ApiResponse


class AppException(Exception):
    """应用统一异常基类"""
    def __init__(self, code: int = 400, message: str = "操作失败"):
        self.code = code
        self.message = message


class AuthException(AppException):
    def __init__(self, message: str = "认证失败"):
        super().__init__(code=401, message=message)


class ForbiddenException(AppException):
    def __init__(self, message: str = "权限不足"):
        super().__init__(code=403, message=message)


class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message)
