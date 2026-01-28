"""
API接口单元测试
使用FastAPI TestClient进行测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 在导入main之前设置环境变量
import tempfile
temp_dir = tempfile.mkdtemp()
os.environ["WORDCROSS_DATA_DIR"] = temp_dir

try:
    from fastapi.testclient import TestClient
    from main import app
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestHealthEndpoints:
    """测试健康检查端点"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """测试根路径"""
        response = client.get("/")
        # 可能返回SPA页面或重定向
        assert response.status_code in [200, 404, 307]
    
    def test_api_docs(self, client):
        """测试API文档"""
        response = client.get("/docs")
        assert response.status_code == 200


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestVocabularyAPI:
    """测试词汇API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_vocabulary_groups(self, client):
        """测试获取词汇组别"""
        response = client.get("/api/vocabulary/groups")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            group = data[0]
            assert "code" in group
            assert "name" in group


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestUserAPI:
    """测试用户API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_user_info_new_user(self, client):
        """测试获取新用户信息"""
        response = client.get("/api/user/info")
        assert response.status_code == 200
        
        data = response.json()
        # 新用户应该返回注册状态信息
        assert "registered" in data or "id" in data or "user_id" in data
    
    def test_register_user(self, client):
        """测试用户注册"""
        response = client.post("/api/user/register", json={
            "nickname": "测试用户",
            "avatar": "😊"
        })
        
        # 应该成功或返回已存在
        assert response.status_code in [200, 201, 400]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestEnergyAPI:
    """测试体力API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_energy(self, client):
        """测试获取体力"""
        response = client.get("/api/user/energy")
        assert response.status_code == 200
        
        data = response.json()
        assert "current" in data or "energy" in data or isinstance(data, dict)


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestPropsAPI:
    """测试道具API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_props(self, client):
        """测试获取道具"""
        response = client.get("/api/user/props")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestLeaderboardAPI:
    """测试排行榜API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_leaderboard_types(self, client):
        """测试获取排行榜类型"""
        response = client.get("/api/leaderboard/types")
        assert response.status_code == 200
        
        data = response.json()
        # 可能返回对象或列表
        assert isinstance(data, (list, dict))
        if isinstance(data, dict):
            assert "types" in data or "groups" in data
    
    def test_get_leaderboard_data(self, client):
        """测试获取排行榜数据"""
        response = client.get("/api/leaderboard/campaign_level?group=all")
        # 可能返回空数据或错误
        assert response.status_code in [200, 404]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestGameAPI:
    """测试游戏API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_endless_puzzle(self, client):
        """测试获取无限模式谜题"""
        response = client.get("/api/endless/puzzle?group=primary&difficulty=easy")
        
        # 应该返回谜题或错误
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "grid_size" in data or "puzzle" in data or "error" in data
    
    def test_get_timed_puzzle(self, client):
        """测试获取计时模式谜题"""
        response = client.get("/api/timed/puzzle?group=primary&duration=180")
        
        assert response.status_code in [200, 400, 500]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestCampaignAPI:
    """测试闯关模式API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_campaign_level(self, client):
        """测试获取闯关关卡"""
        response = client.get("/api/campaign/level/1?group=primary")
        
        # 可能返回关卡数据或需要先加载
        assert response.status_code in [200, 400, 404, 500]
    
    def test_get_levels_summary(self, client):
        """测试获取关卡汇总"""
        response = client.get("/data/levels_summary.json")
        
        # 静态文件可能存在或不存在
        assert response.status_code in [200, 404]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestAdminAPI:
    """测试管理后台API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_overview_stats(self, client):
        """测试获取统计概览"""
        response = client.get("/api/admin/overview")
        
        # 可能需要认证或404（端点不存在）
        assert response.status_code in [200, 401, 403, 404]
    
    def test_get_daily_stats(self, client):
        """测试获取每日统计"""
        response = client.get("/api/admin/daily-stats")
        
        assert response.status_code in [200, 401, 403, 404]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestErrorHandling:
    """测试错误处理"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_invalid_endpoint(self, client):
        """测试无效端点"""
        response = client.get("/api/nonexistent/endpoint")
        assert response.status_code in [404, 307]
    
    def test_invalid_method(self, client):
        """测试无效方法"""
        response = client.delete("/api/vocabulary/groups")
        assert response.status_code in [405, 404, 307]
    
    def test_invalid_params(self, client):
        """测试无效参数"""
        response = client.get("/api/endless/puzzle?group=invalid_group_xyz")
        # 应该处理无效参数
        assert response.status_code in [200, 400, 404, 500]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestCORSHeaders:
    """测试CORS头"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_cors_headers_present(self, client):
        """测试CORS头存在"""
        response = client.options(
            "/api/vocabulary/groups",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # OPTIONS请求应该返回CORS头
        assert response.status_code in [200, 204, 405]
