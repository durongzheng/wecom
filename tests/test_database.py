import pytest
from sqlalchemy import inspect, text, create_engine
from sqlalchemy.exc import IntegrityError, ProgrammingError
from wecom.config import get_settings
from wecom.db import Base, monitor_pool_status, SessionScoped
from wecom.db import Enterprise
import time

@pytest.fixture(scope="module")
def test_db():
    """测试数据库初始化夹具"""
    # 覆盖配置
    settings = get_settings()

    # 创建测试数据库（使用测试配置自动生成的URL）
    admin_engine = create_engine(
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/postgres",
        isolation_level="AUTOCOMMIT"
    )
    
    # 创建测试数据库
    with admin_engine.connect() as conn:
        try:
            conn.execute(text(f"DROP DATABASE IF EXISTS {settings.POSTGRES_DB}"))
            conn.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))
        except ProgrammingError:
            pass  # 忽略已存在的错误

    # 创建测试引擎
    test_engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URL))    
    # 创建所有表
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # 清理测试数据库
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    with admin_engine.connect() as conn:
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{settings.POSTGRES_DB}'
            AND pid <> pg_backend_pid()
        """))
        conn.execute(text(f"DROP DATABASE {settings.POSTGRES_DB}"))

@pytest.fixture
def db_session(test_db):
    """数据库会话夹具"""
    connection = test_db.connect()
    transaction = connection.begin()
    session = SessionScoped(bind=connection)

    # 每次测试前清空所有表
    for table in reversed(Base.metadata.sorted_tables):
        connection.execute(table.delete())
    transaction.commit()
    
    yield session
    
    # 回滚事务并关闭连接
    SessionScoped.remove()
    connection.close()

def test_database_connection(test_db):
    """测试数据库基础连接"""
    with test_db.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1

def test_table_creation(test_db):
    """验证表结构正确性"""
    inspector = inspect(test_db)
    
    # 验证表是否存在
    assert "enterprises" in inspector.get_table_names()
    
    # 验证字段定义
    columns = inspector.get_columns("enterprises")
    column_names = {col["name"] for col in columns}
    expected_columns = {
        "id", "name", "is_active", "api_key", 
        "encrypted_secret", "wecom_corp_id",
        "wecom_secret", "db_cluster", "created_at"
    }
    assert column_names == expected_columns
    
    # 验证主键
    pk_constraint = inspector.get_pk_constraint("enterprises")
    assert pk_constraint["constrained_columns"] == ["id"]

def test_model_crud_operations(db_session):
    """测试基础CRUD操作"""
    # 创建测试数据
    enterprise = Enterprise(
        name="Test Corp",
        api_key="test_api_key",
        encrypted_secret=b"encrypted_data",
        wecom_corp_id="corp_123",
        wecom_secret="secret_456"
    )
    
    # 创建
    db_session.add(enterprise)
    db_session.commit()
    assert enterprise.id is not None
    
    # 读取
    queried = db_session.query(Enterprise).filter_by(name="Test Corp").first()
    assert queried.wecom_corp_id == "corp_123"
    
    # 更新
    queried.db_cluster = "cluster_A"
    db_session.commit()
    updated = db_session.query(Enterprise).get(enterprise.id)
    assert updated.db_cluster == "cluster_A"
    
    # 删除
    db_session.delete(updated)
    db_session.commit()
    assert db_session.query(Enterprise).count() == 0

def test_unique_constraints(db_session):
    """测试唯一性约束"""
    data = {
        "name": "Unique Corp",
        "api_key": "unique_key",
        "encrypted_secret": b"data",
        "wecom_corp_id": "unique_corp",
        "wecom_secret": "unique_secret"
    }
    
    # 第一次插入应该成功
    ent1 = Enterprise(**data)
    db_session.add(ent1)
    db_session.commit()
    
    # 违反唯一性约束
    ent2 = Enterprise(**data)
    db_session.add(ent2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()

def test_connection_pool_management(test_db):
    """测试连接池行为"""
    # 初始化后手动回收所有连接
    test_db.dispose()
    # 初始状态
    assert test_db.pool.checkedin() == 0
    
    # 获取多个连接
    connections = [test_db.connect() for _ in range(3)]
    assert test_db.pool.checkedout() == 3
    
    # 归还连接
    for conn in connections:
        conn.close()
    assert test_db.pool.checkedin() == 3
    
    # 验证连接回收
    monitor_pool_status()  # 可观察控制台输出

def test_transaction_isolation(test_db, db_session):
    """测试事务隔离"""
    # 确保数据库初始为空
    assert db_session.query(Enterprise).count() == 0

    # 事务1插入数据但不提交
    ent = Enterprise(
        name="Transaction Test",
        api_key="tx_key",
        encrypted_secret=b"tx_data",
        wecom_corp_id="tx_corp",
        wecom_secret="tx_secret"
    )
    db_session.add(ent)
    db_session.flush()  # 显式刷新但不提交

    # 使用全新连接验证
    with test_db.connect() as fresh_conn:
        # 必须开启新事务
        with fresh_conn.begin():
            result = fresh_conn.execute(text("SELECT COUNT(*) FROM enterprises"))
            assert result.scalar() == 0

    # 提交事务
    db_session.commit()

    # 再次使用新连接验证
    with test_db.connect() as fresh_conn:
        result = fresh_conn.execute(text("SELECT COUNT(*) FROM enterprises"))
        assert result.scalar() == 1

def test_connection_pool_recycling(test_db, monkeypatch):
    """测试连接回收机制"""
    from sqlalchemy.pool import QueuePool
    
    # 独立配置连接池参数（强制覆盖）
    test_engine = create_engine(
        test_db.url,
        poolclass=QueuePool,
        pool_size=1,
        max_overflow=0,
        pool_recycle=1,  # 设置为1秒快速测试
        pool_pre_ping=True
    )
    
    # 获取初始连接
    conn = test_engine.connect()
    first_conn = conn.connection
    first_conn_id = id(first_conn)
    conn.close()
    
    # 直接让连接过期
    first_conn._pool = test_engine.pool  # 破解内部引用
    first_conn.close = lambda: None  # 禁用正常关闭
    
    # 获取新连接（必须新建）
    new_conn = test_engine.connect()
    new_conn_id = id(new_conn.connection)
    new_conn.close()
    
    # 验证连接ID变化
    assert new_conn_id != first_conn_id, (
        f"连接回收失败 | 初始ID: {first_conn_id} | 新ID: {new_conn_id}"
        f"\n连接状态: {first_conn.closed} | 池状态: {test_engine.pool.status()}"
    )
    
    # 显式清理
    test_engine.dispose()
