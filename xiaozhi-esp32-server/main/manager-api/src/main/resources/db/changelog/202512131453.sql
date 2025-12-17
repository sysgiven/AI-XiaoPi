-- 删除server模块是否开启token认证参数
delete from `sys_params` where param_code = 'server.auth.enabled';

-- 添加server模块是否开启token认证参数
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES 
(122, 'server.auth.enabled', 'true', 'boolean', 1, 'server模块是否开启token认证');