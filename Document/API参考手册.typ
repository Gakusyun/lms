#import "@preview/gakusyun-doc:1.0.0": *

// 设置模板参数
#show: docu.with(
  title: "Leave Management System",
  subtitle: "API 参考手册",
  author: "X. J. Gao",
  show-title: true,
  title-page: false,
  blank-page: false,
  show-index: true,
  index-page: false,
  column-of-index: 2,
  depth-of-index: 2,
  cjk-font: "Source Han Serif",
  emph-cjk-font: "FandolKai",
  latin-font: "New Computer Modern",
  mono-font: "Maple Mono NF",
  default-size: "小四",
  lang: "zh",
  region: "cn",
  paper: "a4",
  margin: 1.2cm,
  date: datetime.today().display("[year]年[month]月[day]日"),
  numbering: "第1页 共1页",
  column: 2,
)

#show raw: set text(size: zh("五号"), font: "Maple Mono NF")

= API 概述

Leave Management System 提供完整的 RESTful API 接口，用于管理学生、教师、审核员、课程和请假记录。

== 基础信息

+ *基础 URL*：`/api/v1/`
+ *数据格式*：JSON
+ *字符编码*：UTF-8
+ *认证方式*：JWT Bearer Token

== 认证机制

系统采用 JWT（JSON Web Token）进行身份认证：

+ *Token 有效期*：30 分钟
+ *Token 包含信息*：
  - `sub`：用户 ID
  - `role`：用户角色（student/teacher/reviewer/admin）
  - `name`：用户姓名
  - `exp`：过期时间戳

+ *使用方式*：
  - 请求头：`Authorization: Bearer {token}`
  - 查询参数：`?token={token}`

== 响应格式

=== 成功响应
```json
{
  "data": { ... }
}
```

=== 错误响应
```json
{
  "detail": "错误信息"
}
```

=== HTTP 状态码
+ *200 OK*：请求成功
+ *400 Bad Request*：请求参数错误
+ *401 Unauthorized*：未授权或 Token 无效
+ *403 Forbidden*：权限不足
+ *404 Not Found*：资源不存在
+ *500 Internal Server Error*：服务器内部错误

= 认证接口

== 用户登录

*POST* `/login`

=== 请求参数
```json
{
  "id": 1,
  "password": "password123"
}
```

=== 响应示例
```json
{
  "role": "student",
  "id": 1,
  "name": "张三",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

=== 说明
+ 验证用户密码（bcrypt）
+ 返回 JWT Token（30分钟有效）
+ 返回用户基本信息

== 检查登录状态

*GET* `/login/check`

=== 请求参数
+ `token`（字符串，必填）：JWT Token

=== 响应示例
```json
{
  "role": "student",
  "id": 1,
  "name": "张三"
}
```

=== 说明
+ 验证 Token 有效性
+ 返回当前登录用户信息

== 用户登出

*GET* `/logout`

=== 请求参数
+ `token`（字符串，必填）：JWT Token

=== 响应示例
```json
{
  "message": "Successfully logged out"
}
```

=== 说明
+ JWT 无状态，登出只需前端删除 Token
+ 后端验证 Token 有效性

== 修改密码

*POST* `/change-password`

=== 请求参数
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "old_password": "oldpass",
  "new_password": "newpass"
}
```

=== 响应示例
```json
{
  "message": "Password changed successfully",
  "target_user_id": 1,
  "target_role": "student"
}
```

=== 说明
+ 修改当前登录用户的密码
+ 需要提供旧密码验证

== 修改指定用户密码（管理员）

*POST* `/change-password/{user_id}`

=== 请求参数
+ `user_id`（路径参数）：目标用户 ID

```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "old_password": "oldpass",
  "new_password": "newpass"
}
```

=== 响应示例
```json
{
  "message": "Password changed successfully",
  "target_user_id": 2,
  "target_role": "student"
}
```

=== 说明
+ 仅管理员可用
+ 可修改任意用户的密码

= 学生管理接口

== 获取学生列表

*GET* `/students`

=== 请求参数
+ `page`（整数，可选）：页码，默认 1
+ `page_size`（整数，可选）：每页数量，默认 20
+ `token`（字符串，必填）：JWT Token

=== 响应示例
```json
{
  "items": [
    {
      "student_id": 1,
      "student_name": "张三",
      "reviewer_id": 1,
      "reviewer_name": "王五",
      "school_id": 1,
      "school_name": "计算机学院"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

== 获取学生总数

*GET* `/students/count`

=== 请求参数
+ `token`（字符串，必填）：JWT Token

=== 响应示例
```json
{
  "students_count": 100
}
```

== 获取学生详情

*GET* `/students/{student_id}`

=== 请求参数
+ `student_id`（路径参数）：学生 ID
+ `token`（字符串，必填）：JWT Token

=== 响应示例
```json
{
  "student_id": 1,
  "student_name": "张三",
  "reviewer_id": 1,
  "school_id": 1
}
```

== 创建学生

*POST* `/students`

=== 请求参数
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "student_id": 1,
  "student_name": "张三",
  "password": "password123",
  "reviewer_id": 1,
  "school_id": 1
}
```

=== 响应示例
```json
{
  "student_id": 1,
  "student_name": "张三",
  "reviewer_id": 1,
  "school_id": 1
}
```

== 更新学生信息

*PUT* `/students/{student_id}`

=== 请求参数
+ `student_id`（路径参数）：学生 ID

```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "student_name": "张三",
  "reviewer_id": 2,
  "school_id": 1
}
```

=== 响应示例
```json
{
  "student_id": 1,
  "student_name": "张三",
  "reviewer_id": 2,
  "school_id": 1
}
```

== 删除学生

*DELETE* `/students/{student_id}`

=== 请求参数
+ `student_id`（路径参数）：学生 ID
+ `token`（字符串，必填）：JWT Token

=== 响应示例
```json
{
  "message": "Student deleted successfully"
}
```

= 教师管理接口

== 获取教师列表

*GET* `/teachers`

=== 请求参数
+ `page`（整数，可选）：页码，默认 1
+ `page_size`（整数，可选）：每页数量，默认 20

=== 响应示例
```json
{
  "items": [
    {
      "teacher_id": 1,
      "teacher_name": "李四"
    }
  ],
  "total": 20,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

== 获取教师总数

*GET* `/teachers/count`

=== 响应示例
```json
{
  "teachers_count": 20
}
```

== 获取教师详情

*GET* `/teachers/{teacher_id}`

=== 请求参数
+ `teacher_id`（路径参数）：教师 ID

=== 响应示例
```json
{
  "teacher_id": 1,
  "teacher_name": "李四"
}
```

== 创建教师

*POST* `/teachers`

=== 请求参数
```json
{
  "teacher_id": 1,
  "teacher_name": "李四",
  "password": "password123"
}
```

=== 响应示例
```json
{
  "teacher_id": 1,
  "teacher_name": "李四"
}
```

== 更新教师信息

*PUT* `/teachers/{teacher_id}`

=== 请求参数
+ `teacher_id`（路径参数）：教师 ID

```json
{
  "teacher_name": "李四（更新）"
}
```

=== 响应示例
```json
{
  "teacher_id": 1,
  "teacher_name": "李四（更新）"
}
```

== 删除教师

*DELETE* `/teachers/{teacher_id}`

=== 请求参数
+ `teacher_id`（路径参数）：教师 ID

=== 响应示例
```json
{
  "message": "Teacher deleted successfully"
}
```

= 审核员管理接口

== 获取审核员列表

*GET* `/reviewers`

=== 请求参数
+ `page`（整数，可选）：页码，默认 1
+ `page_size`（整数，可选）：每页数量，默认 20

=== 响应示例
```json
{
  "items": [
    {
      "reviewer_id": 1,
      "reviewer_name": "王五",
      "school_id": 1,
      "school_name": "计算机学院",
      "role_id": 2,
      "role_name": "审核员"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

== 创建审核员

*POST* `/reviewers`

=== 请求参数
```json
{
  "reviewer_id": 1,
  "reviewer_name": "王五",
  "password": "password123",
  "school_id": 1,
  "role_id": 2
}
```

=== 响应示例
```json
{
  "reviewer_id": 1,
  "reviewer_name": "王五",
  "school_id": 1,
  "role_id": 2
}
```

== 更新审核员信息

*PUT* `/reviewers/{reviewer_id}`

=== 请求参数
+ `reviewer_id`（路径参数）：审核员 ID

```json
{
  "reviewer_name": "王五（更新）",
  "school_id": 1,
  "role_id": 2
}
```

=== 响应示例
```json
{
  "reviewer_id": 1,
  "reviewer_name": "王五（更新）",
  "school_id": 1,
  "role_id": 2
}
```

== 删除审核员

*DELETE* `/reviewers/{reviewer_id}`

=== 请求参数
+ `reviewer_id`（路径参数）：审核员 ID

=== 响应示例
```json
{
  "message": "Reviewer deleted successfully"
}
```

= 课程管理接口

== 获取课程列表

*GET* `/courses`

=== 请求参数
+ `page`（整数，可选）：页码，默认 1
+ `page_size`（整数，可选）：每页数量，默认 20

=== 响应示例
```json
{
  "items": [
    {
      "course_id": 1,
      "course_name": "高等数学",
      "teacher_id": 1,
      "teacher_name": "李四",
      "enrollment_count": 50
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

== 创建课程

*POST* `/courses`

=== 请求参数
```json
{
  "course_id": 1,
  "course_name": "高等数学",
  "teacher_id": 1
}
```

=== 响应示例
```json
{
  "course_id": 1,
  "course_name": "高等数学",
  "teacher_id": 1
}
```

== 更新课程信息

*PUT* `/courses/{course_id}`

=== 请求参数
+ `course_id`（路径参数）：课程 ID

```json
{
  "course_name": "高等数学（修订版）",
  "teacher_id": 1
}
```

=== 响应示例
```json
{
  "course_id": 1,
  "course_name": "高等数学（修订版）",
  "teacher_id": 1
}
```

== 删除课程

*DELETE* `/courses/{course_id}`

=== 请求参数
+ `course_id`（路径参数）：课程 ID

=== 响应示例
```json
{
  "message": "Course deleted successfully"
}
```

= 请假管理接口

== 获取请假列表

*GET* `/leaves`

=== 请求参数
+ `token`（字符串，必填）：JWT Token
+ `page`（整数，可选）：页码，默认 1
+ `page_size`（整数，可选）：每页数量，默认 20

=== 响应示例
```json
{
  "items": [
    {
      "leave_id": 1,
      "student_id": 1,
      "student_name": "张三",
      "leave_date": "2024-01-01T00:00:00",
      "status": "待审批",
      "leave_type": "事假",
      "remarks": "家里有事",
      "reviewer_id": 1,
      "reviewer_name": "王五",
      "course_id": 1,
      "course_name": "高等数学"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

== 创建请假条

*POST* `/leaves`

=== 请求参数
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "leave_date": "2024-01-01T00:00:00",
  "leave_hours": "2",
  "leave_type": "事假",
  "remarks": "家里有事",
  "course_id": 1,
  "guarantee_student_id": 2
}
```

=== 响应示例
```json
{
  "leave_id": 1,
  "student_id": 1,
  "leave_date": "2024-01-01T00:00:00",
  "status": "待审批",
  "leave_type": "事假",
  "remarks": "家里有事",
  "course_id": 1,
  "guarantee_student_id": 2
}
```

=== 请假类型
+ `事假`：个人事务
+ `病假`：因病请假
+ `公假`：公务请假
+ `婚假`：结婚请假
+ `丧假`：丧事请假

=== 请假状态
+ `待审批`：等待审核员审核
+ `已批准`：审核通过
+ `已拒绝`：审核未通过
+ `已撤销`：用户主动撤销

== 编辑/审核请假条

*POST* `/leaves/edit/{leave_id}`

=== 请求参数
+ `leave_id`（路径参数）：请假条 ID

=== 审核操作（审核员）
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "status": "已批准",
  "audit_remarks": "批准"
}
```

=== 编辑操作（学生）
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "leave_type": "病假",
  "remarks": "身体不适"
}
```

=== 响应示例
```json
{
  "leave_id": 1,
  "status": "已批准",
  "audit_remarks": "批准",
  "audit_time": "2024-01-01T10:00:00"
}
```

=== 说明
+ 审核员可修改状态和添加审核备注
+ 学生只能编辑待审批状态的请假条
+ 审核后自动记录审核时间

= 学生选课接口

== 学生选课

*POST* `/student-courses`

=== 请求参数
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "student_id": 1,
  "course_id": 1,
  "enrollment_date": "2024-01-01",
  "status": "已选课"
}
```

=== 响应示例
```json
{
  "student_id": 1,
  "course_id": 1,
  "enrollment_date": "2024-01-01",
  "status": "已选课"
}
```

== 学生退课

*DELETE* `/student-courses/student/{student_id}/course/{course_id}`

=== 请求参数
+ `student_id`（路径参数）：学生 ID
+ `course_id`（路径参数）：课程 ID
+ `token`（查询参数，必填）：JWT Token

=== 响应示例
```json
{
  "message": "Course dropped successfully"
}
```

== 获取学生选课列表

*GET* `/student-courses/student/{student_id}`

=== 请求参数
+ `student_id`（路径参数）：学生 ID

=== 响应示例
```json
{
  "courses": [
    {
      "course_id": 1,
      "course_name": "高等数学",
      "enrollment_date": "2024-01-01",
      "status": "已选课"
    }
  ]
}
```

== 获取课程学生列表

*GET* `/student-courses/course/{course_id}`

=== 请求参数
+ `course_id`（路径参数）：课程 ID

=== 响应示例
```json
{
  "students": [
    {
      "student_id": 1,
      "student_name": "张三",
      "enrollment_date": "2024-01-01",
      "status": "已选课"
    }
  ]
}
```

== 获取课程选课人数

*GET* `/student-courses/course/{course_id}/count`

=== 请求参数
+ `course_id`（路径参数）：课程 ID

=== 响应示例
```json
{
  "enrollment_count": 50
}
```

= 统计分析接口

== 获取请假统计

*GET* `/statistics/leaves`

=== 请求参数
+ `token`（字符串，必填）：JWT Token

=== 响应示例
```json
{
  "leave_statistics": [
    {"status": "待审批", "count": 10},
    {"status": "已批准", "count": 50},
    {"status": "已拒绝", "count": 5},
    {"status": "已撤销", "count": 2}
  ]
}
```

== 获取请假趋势

*GET* `/statistics/leaves/trend`

=== 请求参数
+ `token`（字符串，必填）：JWT Token
+ `days`（整数，可选）：统计天数，默认 30

=== 响应示例
```json
{
  "leave_trend": [
    {"date": "2024-01-01", "count": 5},
    {"date": "2024-01-02", "count": 8},
    {"date": "2024-01-03", "count": 3}
  ]
}
```

== 获取课程选课统计

*GET* `/statistics/courses/enrollment`

=== 请求参数
+ `token`（字符串，必填）：JWT Token

=== 响应示例
```json
{
  "enrollment_statistics": [
    {"course_id": 1, "course_name": "高等数学", "enrollment_count": 50},
    {"course_id": 2, "course_name": "英语", "enrollment_count": 45}
  ]
}
```

== 获取用户统计

*GET* `/statistics/users`

=== 响应示例
```json
{
  "user_statistics": {
    "students": 100,
    "teachers": 20,
    "reviewers": 5
  }
}
```

== 获取审核员绩效

*GET* `/statistics/reviewers/performance`

=== 请求参数
+ `token`（字符串，必填）：JWT Token

=== 响应示例
```json
{
  "reviewer_performance": [
    {
      "reviewer_id": 1,
      "reviewer_name": "王五",
      "total_leaves": 20,
      "approved_leaves": 15,
      "rejected_leaves": 5,
      "approval_rate": 75.0
    }
  ]
}
```

= 数据备份接口

== 导出数据

*POST* `/backup/export`

=== 响应示例
```json
{
  "message": "Data exported successfully",
  "data": {
    "students": [...],
    "teachers": [...],
    "reviewers": [...],
    "courses": [...],
    "leaves": [...]
  }
}
```

== 导入数据

*POST* `/backup/import`

=== 请求参数
```json
{
  "data": {
    "students": [...],
    "teachers": [...],
    ...
  }
}
```

=== 响应示例
```json
{
  "message": "Data imported successfully",
  "imported": {
    "students": 100,
    "teachers": 20,
    "reviewers": 5,
    "courses": 10,
    "leaves": 200
  }
}
```

= 系统接口

== 健康检查

*GET* `/health`

=== 响应示例
```json
{
  "status": "healthy"
}
```

== 根路径

*GET* `/`

=== 响应示例
```json
{
  "message": "Leave Management System API",
  "version": "1.0.0"
}
```

= 错误处理

== 标准错误响应

所有错误响应遵循统一格式：

```json
{
  "detail": "错误信息描述"
}
```

== 常见错误

=== 400 Bad Request
```json
{
  "detail": "Invalid input: field 'student_name' is required"
}
```

=== 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

=== 403 Forbidden
```json
{
  "detail": "Permission denied"
}
```

=== 404 Not Found
```json
{
  "detail": "Student not found"
}
```

=== 500 Internal Server Error
```json
{
  "detail": "Internal server error, please try again later"
}
```

= 附录

== 日期时间格式

所有日期时间字段使用 ISO 8601 格式：

```
2024-01-01T00:00:00
```

== 分页参数

所有列表接口支持分页：

+ `page`：页码（从 1 开始）
+ `page_size`：每页数量（默认 20）

响应包含分页信息：

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

== Token 刷新

Token 有效期为 30 分钟，过期后需要重新登录。前端应：

1. 监听 401 错误
2. 清除本地存储的 Token
3. 跳转到登录页

== Swagger 文档

启动后端服务后，访问以下地址查看交互式 API 文档：

+ Swagger UI：`http://localhost:8000/docs`
+ ReDoc：`http://localhost:8000/redoc`
