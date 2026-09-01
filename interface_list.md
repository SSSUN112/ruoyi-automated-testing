## L01 登录接口

- 方法：POST

- 路径：/login

- 鉴权：不需要

- 参数：

  ```
  {
    "username": "string",
    "password": "string",
  }
  ```

### 正常响应

- code：200
- msg：登录成功
- token：“******* ”

### 异常响应

- 密码错误：
  - “code”：601
  - “msg”：“密码错误”
  - "success":false
  - "time":"2026-07-20T09:17:09.297280"

- 用户不存在：
  - “code”：601
  - “msg”：“用户不存在”
  - "success":false
  - "time":"2026-07-20T09:17:09.297280"

## U01 获取用户列表

- 方法：GET
- 路径：/system/user/list
- 鉴权：需要
- 参数：
  - pageNum：query，必填/默认值待确认
  - pageSize：query，必填/默认值待确认
  - userName：query，可选

### 正常响应

- code：200
- success：true
- data：
  - rows：用户数组
  - total：总数量

### 异常响应

- 未登录：
  - "code":401
  - "msg":"用户未登录，请先完成登录"
  - "success":false

## U02 编辑用户

- 方法：PUT

- 路径：/system/user

- 鉴权：需要

- 参数：

  - ```json
    {
      "userId": 0,
      "deptId": 0,
      "userName": "string",
      "nickName": "string",
      "userType": "string",
      "email": "string",
      "phonenumber": "string",
      "sex": "0",
      "avatar": "string",
      "password": "string",
      "status": "0",
      "delFlag": "0",
      "loginIp": "string",
      "loginDate": "2026-07-20T12:29:04.058Z",
      "pwdUpdateDate": "2026-07-20T12:29:04.058Z",
      "createBy": "string",
      "createTime": "2026-07-20T12:29:04.058Z",
      "updateBy": "string",
      "updateTime": "2026-07-20T12:29:04.058Z",
      "remark": "string",
      "admin": false,
      "roleIds": [],
      "postIds": [],
      "type": "string",
      "role": []
    }
    ```

### 正常响应

{
  "code": 200,
  "msg": "操作成功",
  "success": true,
  "time": "2026-07-20T12:29:04.123Z"
}

### 数据库断言

