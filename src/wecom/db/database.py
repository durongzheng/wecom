# database.py 优化版
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
from ..config import get_settings
import logging
import time

# 获取配置
settings = get_settings()
Base = declarative_base()

# 连接池配置参数
POOL_CONFIG = {
    "pool_size": settings.POOL_SIZE,        # 常驻连接数
    "max_overflow": settings.MAX_OVERFLOW,      # 最大溢出连接数
    "pool_recycle": settings.POOL_RECYCLE,   # 连接回收时间（秒）
    "pool_pre_ping": settings.POOL_PRE_PING,  # 执行前健康检查
    "pool_timeout": settings.POOL_TIMEOUT,     # 获取连接超时时间
    "echo_pool": settings.ECHO_POOL      # 调试时开启
}

def setup_connection_pool():
    """创建带连接池的引擎"""
    # 构建连接字符串
    conn_str = settings.SQLALCHEMY_DATABASE_URL
    
    # 创建带连接池的引擎
    engine = create_engine(
        conn_str,
        poolclass=QueuePool,  # 使用队列连接池
        ​**POOL_CONFIG,
        connect_args={
            "connect_timeout": 10,      # 连接超时设置
            "keepalives_idle": 30,      # TCP保活
            "options": "-c statement_timeout=5000"  # 查询超时5秒
        }
    )
    
    # 添加连接池事件监听
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_conn, connection_record, connection_proxy):
        """连接取出时记录"""
        logging.debug("Connection checked out: %s", id(dbapi_conn))
        
    @event.listens_for(engine, "checkin")
    def on_checkin(dbapi_conn, connection_record):
        """连接归还时记录"""
        logging.debug("Connection checked in: %s", id(dbapi_conn))
    
    return engine

# 初始化引擎
engine = setup_connection_pool()

# 创建线程安全的会话工厂
SessionFactory = sessionmaker(bind=engine, autoflush=False)

# 使用scoped_session管理线程局部会话
SessionScoped = scoped_session(SessionFactory)

def get_db():
    """
    获取数据库会话（微服务安全版）
    使用示例：
    with get_db() as db:
        db.query(...)
    """
    db = SessionScoped()
    try:
        yield db
    except Exception as e:
        logging.error("Database error: %s", str(e))
        db.rollback()
        raise
    finally:
        # 关闭会话时自动归还连接到池
        SessionScoped.remove()

# 监控连接池状态
def monitor_pool_status():
    """打印连接池状态（可用于定时任务）"""
    print(f"[Pool Status] {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current checked out connections: {engine.pool.checkedout()}")
    print(f"Current idle connections: {engine.pool.checkedin()}")
    print(f"Total connections: {engine.pool.size() + engine.pool.overflow()}")