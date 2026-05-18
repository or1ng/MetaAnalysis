def success_response(data=None, message: str = "success"):
    """统一成功响应"""
    return {"code": 200, "message": message, "data": data}


def error_response(code: int = 400, message: str = "请求失败", data=None):
    """统一错误响应"""
    return {"code": code, "message": message, "data": data}


class ApiResponse:
    """响应工具类"""
    @staticmethod
    def ok(data=None, message: str = "success"):
        return success_response(data, message)

    @staticmethod
    def fail(message: str = "请求失败", code: int = 400, data=None):
        return error_response(code, message, data)

    @staticmethod
    def not_found(message: str = "资源不存在"):
        return error_response(404, message)

    @staticmethod
    def unauthorized(message: str = "未授权，请先登录"):
        return error_response(401, message)

    @staticmethod
    def forbidden(message: str = "权限不足"):
        return error_response(403, message)

    @staticmethod
    def server_error(message: str = "服务器内部错误"):
        return error_response(500, message)
