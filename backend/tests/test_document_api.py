from pathlib import Path

import aiosqlite
from app.database import get_db
from app.main import app
from fastapi.testclient import TestClient

# 使用内存数据库
TEST_DB = ":memory:"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"

# 保存数据库连接
_db = None


# 初始化数据库
async def init_test_db():
    global _db
    if _db is None:
        _db = await aiosqlite.connect(TEST_DB)
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            await _db.executescript(f.read())
        await _db.execute("PRAGMA foreign_keys = ON")
        _db.row_factory = aiosqlite.Row
    return _db


async def get_test_db():
    db = await init_test_db()
    try:
        yield db
    except Exception:
        await db.rollback()
        raise
    else:
        await db.commit()


# 覆盖原有的数据库依赖
app.dependency_overrides[get_db] = get_test_db


def test_document_workflow():
    """测试文档相关的所有接口流程"""
    client = TestClient(app)

    # 1. 创建测试文件
    test_content = "测试文档内容"
    test_file = Path("temp_test.txt")
    test_file.write_text(test_content)

    try:
        # 2. 测试上传文档 - POST /api/knowledge/upload
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/knowledge/upload",
                files={"file": ("test.txt", f, "text/plain")},
                data={"type": "text", "description": "测试文档"},
            )
        assert response.status_code == 200
        doc_data = response.json()
        doc_id = doc_data["id"]
        assert doc_data["filename"] == "test.txt"
        assert doc_data["status"] == "processing"
        assert doc_data["type"] == "text"

        # 3. 测试获取文档状态 - GET /api/knowledge/status/{document_id}
        response = client.get(f"/api/knowledge/status/{doc_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["id"] == doc_id
        assert "status" in status_data
        assert "progress" in status_data
        assert "message" in status_data

        # 4. 测试获取文档列表 - GET /api/knowledge/list
        response = client.get("/api/knowledge/list")
        assert response.status_code == 200
        list_data = response.json()
        assert "documents" in list_data
        assert len(list_data["documents"]) > 0

        # 测试带过滤条件的文档列表
        response = client.get("/api/knowledge/list", params={"type": "text"})
        assert response.status_code == 200
        filtered_data = response.json()
        assert all(doc["type"] == "text" for doc in filtered_data["documents"])

        # 5. 测试更新文档信息 - PUT /api/knowledge/{document_id}
        update_data = {"new_name": "updated_test.txt", "enabled": False}
        response = client.put(f"/api/knowledge/{doc_id}", json=update_data)
        assert response.status_code == 200
        updated_doc = response.json()
        assert updated_doc["filename"] == "updated_test.txt"
        assert updated_doc["enabled"] is False

        # 6. 测试删除文档 - DELETE /api/knowledge/{document_id}
        response = client.delete(f"/api/knowledge/{doc_id}")
        assert response.status_code == 200
        delete_result = response.json()
        assert delete_result["success"] is True
        assert "文档已成功删除" in delete_result["message"]

        # 7. 验证文档已被删除
        response = client.get(f"/api/knowledge/status/{doc_id}")
        assert response.status_code == 404
        assert "文档不存在" in response.json()["detail"]

        # 8. 测试错误情况
        # 8.1 获取不存在的文档
        response = client.get("/api/knowledge/status/nonexistent")
        assert response.status_code == 404
        assert "文档不存在" in response.json()["detail"]

        # 8.2 更新不存在的文档
        response = client.put("/api/knowledge/nonexistent", json=update_data)
        assert response.status_code == 404

        # 8.3 删除不存在的文档
        response = client.delete("/api/knowledge/nonexistent")
        assert response.status_code == 404

    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_document_workflow()
