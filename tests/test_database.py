import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from wecom.config import get_settings
from wecom.db import Base, engine, get_db, monitor_pool_status, SessionScoped, POOL_CONFIG
from wecom.db import Enterprise
import time

@pytest.fixture(scope="module")
def test_db():
    """测试数据库初始化夹具（模块级）"""
    # 使用临时测试数据库（通过修改环境变量实现）
    settings = get_settings()
    original_db = settings.POSTGRES_DB
    settings.POSTGRES_DB = "test_" + original_db  # 创建测试数据库

    # 创建测试数据库（需要主数据库连接权限）
    with engine.connect() as conn:
        try:
            conn.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))
        except ProgrammingError:
            conn.rollback()
    
    # 重新创建引擎指向测试数据库
    test_engine = create_engine(
        conn_str,
        poolclass=QueuePool,
        **POOL_CONFIG,
        connect_args={
            "connect_timeout": 10,
            "keepalives_idle": 30,
            "options": "-c statement_timeout=5000"
        }
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # 清理测试数据库
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    with engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE {settings.POSTGRES_DB}"))

@pytest.fixture
def db_session(test_db):
    """数据库会话夹具"""
    connection = test_db.connect()
    transaction = connection.begin()
    session = SessionScoped(bind=connection)
    
    yield session
    
    # 回滚事务并关闭连接
    SessionScoped.remove()
    transaction.rollback()
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

def test_transaction_isolation(db_session):
    """测试事务隔离"""
    # 事务1插入数据但不提交
    ent = Enterprise(
        name="Transaction Test",
        api_key="tx_key",
        encrypted_secret=b"tx_data",
        wecom_corp_id="tx_corp",
        wecom_secret="tx_secret"
    )
    db_session.add(ent)
    
    # 在另一个连接中查询应该看不到未提交数据
    with test_db.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM enterprises"))
        assert result.scalar() == 0
    
    # 提交后应可见
    db_session.commit()
    with test_db.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM enterprises"))
        assert result.scalar() == 1

def test_connection_pool_recycling(test_db, monkeypatch):
    """测试连接回收机制"""
    # 获取初始连接
    conn = test_db.connect()
    first_conn_id = id(conn.connection)
    conn.close()
    
    # 模拟超过回收时间
    monkeypatch.setattr("time.time", lambda: time.time() + 2000)
    
    # 获取新连接应触发回收
    new_conn = test_db.connect()
    assert id(new_conn.connection) != first_conn_id
    new_conn.close()