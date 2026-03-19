# API变更文档

## 1. 认证机制变更

### 1.1 登录接口 (`/api/v1/login`)
- **变更**: 从使用前端提供的token改为后端生成JWT token
- **返回值变化**:
  - 现在返回的`token`字段是JWT格式的令牌
  - token包含过期时间（30分钟）

### 1.2 登录状态检查接口 (`/api/v1/login/check`)
- **变更**: 从基于数据库的token验证改为JWT验证
- **行为变化**:
  - 验证token的有效性和过期时间
  - 不再依赖数据库中的`Login`表记录

### 1.3 登出接口 (`/api/v1/logout`)
- **变更**: 从更新数据库记录改为无状态操作
- **行为变化**:
  - 验证token有效性
  - 前端只需删除本地存储的token即可完成登出

## 2. 密码处理变更

### 2.1 密码哈希算法
- **变更**: 从直接使用bcrypt改为使用passlib库
- **影响**: 无API层面的变更，仅为内部实现优化

## 3. CORS配置变更

### 3.1 CORS中间件配置
- **变更**: 从允许所有来源改为从配置文件读取允许的来源
- **允许的来源**:
  - 开发环境: `http://localhost:3000`, `http://127.0.0.1:3000`
  - 生产环境: `http://gxj62.cn`, `https://gxj62.cn`, `http://*.gxj62.cn`, `https://*.gxj62.cn`, `http://gkux.cn`, `https://gkux.cn`, `http://*.gkux.cn`, `https://*.gkux.cn`
- **允许的HTTP方法**:
  - GET, POST, PUT, DELETE, OPTIONS
- **允许的请求头**:
  - Content-Type
  - Authorization
- **配置方式**:
  - 在 `config.toml` 文件的 `[cors]` 部分配置 `origins` 列表

## 4. 其他变更

### 4.1 依赖管理
- **变更**: 使用uv管理依赖
- **新增依赖**:
  - python-jose[cryptography]: 用于JWT处理
  - passlib[bcrypt]: 用于密码哈希
  - alembic: 用于数据库迁移（准备中）

### 4.2 数据库配置
- **变更**: 优化数据库连接池配置
- **配置参数**:
  - pool_pre_ping: True
  - pool_size: 10
  - max_overflow: 20
  - pool_timeout: 30
  - pool_recycle: 1800

## 5. 前端适配建议

1. **登录流程**:
   - 调用登录接口获取JWT token
   - 将token存储在本地存储中
   - 在后续请求的Authorization头中携带token

2. **请求头设置**:
   ```javascript
   headers: {
     'Authorization': `Bearer ${token}`,
     'Content-Type': 'application/json'
   }
   ```

3. **token过期处理**:
   - 监听401错误
   - 当收到"Invalid or expired token"错误时，重新登录

4. **登出流程**:
   - 删除本地存储的token
   - 无需等待后端响应

5. **CORS配置**:
   - 确保前端开发服务器运行在`http://localhost:3000`或`http://127.0.0.1:3000`

## 6. 注意事项

- JWT token包含敏感信息，应通过HTTPS传输
- 前端应定期检查token是否即将过期，并在过期前刷新
- 所有API请求都需要在查询参数中携带`token`参数，或在请求头中携带`Authorization`头

## 7. 测试建议

1. 测试登录接口获取JWT token
2. 测试使用token访问受保护的API
3. 测试token过期后的行为
4. 测试登出功能
5. 测试密码修改功能