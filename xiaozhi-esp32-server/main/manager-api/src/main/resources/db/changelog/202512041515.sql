-- liquibase formatted sql

-- changeset xiaozhi:202512041515
CREATE TABLE ai_agent_context_provider (
    id VARCHAR(32) NOT NULL COMMENT '主键',
    agent_id VARCHAR(32) NOT NULL COMMENT '智能体ID',
    context_providers JSON COMMENT '上下文源配置',
    creator BIGINT COMMENT '创建者',
    created_at DATETIME COMMENT '创建时间',
    updater BIGINT COMMENT '更新者',
    updated_at DATETIME COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_agent_id (agent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体上下文源配置表';
