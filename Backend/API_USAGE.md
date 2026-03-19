# API使用说明

## 1. 认证相关API

### 1.1 登录
- **端点**: `POST /api/v1/login`
- **参数**:
  - `id`: 整数，用户ID
  - `password`: 字符串，密码
- **响应**:
  ```json
  {
    "role": "student",
    "id": 1,
    "name": "张三",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

### 1.2 检查登录状态
- **端点**: `GET /api/v1/login/check`
- **参数**:
  - `token`: 字符串，JWT token
- **响应**:
  ```json
  {
    "role": "student",
    "id": 1,
    "name": "张三"
  }
  ```

### 1.3 登出
- **端点**: `GET /api/v1/logout`
- **参数**:
  - `token`: 字符串，JWT token
- **响应**:
  ```json
  {"message": "Logout successful"}
  ```

### 1.4 注册
- **端点**: `POST /api/v1/register`
- **参数**:
  - `role`: 字符串，用户角色 (student/teacher/reviewer/admin)
  - `id`: 整数，用户ID
  - `name`: 字符串，用户名
  - `password`: 字符串，密码
- **响应**:
  ```json
  {
    "message": "Registration successful",
    "role": "student",
    "id": 1,
    "name": "张三"
  }
  ```

### 1.5 修改密码
- **端点**: `POST /api/v1/change-password`
- **参数**:
  - `token`: 字符串，JWT token
  - `old_password`: 字符串，旧密码
  - `new_password`: 字符串，新密码
- **响应**:
  ```json
  {
    "message": "Password changed successfully",
    "target_user_id": 1,
    "target_role": "student"
  }
  ```

## 2. 课程相关API

### 2.1 获取课程列表
- **端点**: `GET /api/v1/courses`
- **参数**:
  - `page`: 整数，页码（默认1）
  - `page_size`: 整数，每页数量（默认20）
- **响应**:
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

### 2.2 创建课程
- **端点**: `POST /api/v1/courses`
- **参数**:
  - `course_id`: 整数，课程ID
  - `course_name`: 字符串，课程名称
  - `teacher_id`: 整数，教师ID
- **响应**:
  ```json
  {
    "course_id": 1,
    "course_name": "高等数学",
    "teacher_id": 1
  }
  ```

### 2.3 编辑课程
- **端点**: `PUT /api/v1/courses/{course_id}`
- **参数**:
  - `course_name`: 字符串，课程名称
  - `teacher_id`: 整数，教师ID
- **响应**:
  ```json
  {
    "course_id": 1,
    "course_name": "高等数学（修订版）",
    "teacher_id": 1
  }
  ```

### 2.4 删除课程
- **端点**: `DELETE /api/v1/courses/{course_id}`
- **响应**:
  ```json
  {"message": "Course deleted successfully"}
  ```

## 3. 请假相关API

### 3.1 获取请假列表
- **端点**: `GET /api/v1/leaves`
- **参数**:
  - `token`: 字符串，JWT token
  - `page`: 整数，页码（默认1）
  - `page_size`: 整数，每页数量（默认20）
- **响应**:
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
    "total": 5,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
  ```

### 3.2 创建请假
- **端点**: `POST /api/v1/leaves`
- **参数**:
  - `token`: 字符串，JWT token
  - `leave_date`: 日期时间，请假日期
  - `leave_hours`: 字符串，请假时长
  - `leave_type`: 字符串，请假类型
  - `remarks`: 字符串，请假原因
  - `course_id`: 整数，课程ID
  - `guarantee_student_id`: 整数，担保人学生ID
- **响应**:
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

### 3.3 批准请假
- **端点**: `POST /api/v1/leaves/approve/{leave_id}`
- **参数**:
  - `token`: 字符串，JWT token
  - `audit_remarks`: 字符串，审批备注
- **响应**:
  ```json
  {
    "leave_id": 1,
    "status": "已批准",
    "audit_remarks": "批准",
    "audit_time": "2024-01-01T10:00:00"
  }
  ```

### 3.4 拒绝请假
- **端点**: `POST /api/v1/leaves/reject/{leave_id}`
- **参数**:
  - `token`: 字符串，JWT token
  - `audit_remarks`: 字符串，审批备注
- **响应**:
  ```json
  {
    "leave_id": 1,
    "status": "已拒绝",
    "audit_remarks": "理由不充分",
    "audit_time": "2024-01-01T10:00:00"
  }
  ```

## 4. 学生-课程关联API

### 4.1 学生选课
- **端点**: `POST /api/v1/student-courses`
- **参数**:
  - `token`: 字符串，JWT token
  - `student_id`: 整数，学生ID
  - `course_id`: 整数，课程ID
  - `enrollment_date`: 日期，选课日期
  - `status`: 字符串，选课状态
- **响应**:
  ```json
  {
    "student_id": 1,
    "course_id": 1,
    "enrollment_date": "2024-01-01",
    "status": "已选课"
  }
  ```

### 4.2 学生退课
- **端点**: `DELETE /api/v1/student-courses/student/{student_id}/course/{course_id}`
- **参数**:
  - `token`: 字符串，JWT token
- **响应**:
  ```json
  {"message": "Course dropped successfully"}
  ```

## 5. 审核人相关API

### 5.1 获取审核人列表
- **端点**: `GET /api/v1/reviewers`
- **参数**:
  - `page`: 整数，页码（默认1）
  - `page_size`: 整数，每页数量（默认20）
- **响应**:
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
    "total": 3,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
  ```

### 5.2 创建审核人
- **端点**: `POST /api/v1/reviewers`
- **参数**:
  - `reviewer_id`: 整数，审核员ID
  - `reviewer_name`: 字符串，审核员姓名
  - `password`: 字符串，密码
  - `school_id`: 整数，学校ID
  - `role_id`: 整数，角色ID
- **响应**:
  ```json
  {
    "reviewer_id": 1,
    "reviewer_name": "王五",
    "school_id": 1,
    "role_id": 2
  }
  ```

## 6. 统计相关API

### 6.1 获取请假统计
- **端点**: `GET /api/v1/statistics/leaves`
- **参数**:
  - `token`: 字符串，JWT token
- **响应**:
  ```json
  {
    "leave_statistics": [
      {"status": "待审批", "count": 2},
      {"status": "已批准", "count": 5},
      {"status": "已拒绝", "count": 1}
    ]
  }
  ```

### 6.2 获取请假趋势
- **端点**: `GET /api/v1/statistics/leaves/trend`
- **参数**:
  - `token`: 字符串，JWT token
  - `days`: 整数，天数（默认30）
- **响应**:
  ```json
  {
    "leave_trend": [
      {"date": "2024-01-01", "count": 1},
      {"date": "2024-01-02", "count": 2}
    ]
  }
  ```

### 6.3 获取课程选课统计
- **端点**: `GET /api/v1/statistics/courses/enrollment`
- **参数**:
  - `token`: 字符串，JWT token
- **响应**:
  ```json
  {
    "enrollment_statistics": [
      {"course_id": 1, "course_name": "高等数学", "enrollment_count": 50},
      {"course_id": 2, "course_name": "英语", "enrollment_count": 45}
    ]
  }
  ```

### 6.4 获取用户统计
- **端点**: `GET /api/v1/statistics/users`
- **响应**:
  ```json
  {
    "user_statistics": {
      "students": 100,
      "teachers": 20,
      "reviewers": 5
    }
  }
  ```

### 6.5 获取审核员绩效
- **端点**: `GET /api/v1/statistics/reviewers/performance`
- **参数**:
  - `token`: 字符串，JWT token
- **响应**:
  ```json
  {
    "reviewer_performance": [
      {
        "reviewer_id": 1,
        "reviewer_name": "王五",
        "total_leaves": 10,
        "approved_leaves": 8,
        "rejected_leaves": 2,
        "approval_rate": 80.0
      }
    ]
  }
  ```

## 7. 通用参数

- 所有需要认证的API都需要在查询参数中携带 `token` 参数，或在请求头中携带 `Authorization` 头，格式为 `Bearer {token}`
- 分页参数：`page`（页码，默认1）和 `page_size`（每页数量，默认20）
- 日期时间格式：ISO 8601 格式，如 `2024-01-01T00:00:00`

## 8. 错误处理

- 400: 请求参数错误
- 401: 未授权，token无效或过期
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误

错误响应格式：
```json
{
  "detail": "错误信息"
}
```
