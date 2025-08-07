import pytest
from datetime import date, datetime
from app.services.content_service import ContentService
from app.schemas.news_article import NewsArticleCreate, NewsArticleResponse
from app.schemas.video import VideoCreate, VideoResponse, VideoType
from app.schemas.system_setting import SystemSettingCreate, SystemSettingResponse


class TestContentService:
    """Unit tests for ContentService"""

    @pytest.fixture
    def sample_article_data(self):
        """Sample article data for testing"""
        return NewsArticleCreate(
            title="Test Article",
            content="This is a test article content",
            author_id=None,
            image_url="https://example.com/image.jpg",
            is_featured=True,
            is_active=True,
            publish_date=date.today(),
            expiry_date=None,
        )

    @pytest.fixture
    def sample_video_data(self):
        """Sample video data for testing"""
        return VideoCreate(
            title="Test Video",
            description="This is a test video description",
            video_url="https://example.com/video.mp4",
            thumbnail_url="https://example.com/thumbnail.jpg",
            video_type=VideoType.INFORMATIONAL,
            is_featured=False,
            is_active=True,
            publish_date=date.today(),
            expiry_date=None,
        )

    @pytest.fixture
    def sample_setting_data(self):
        """Sample system setting data for testing"""
        return SystemSettingCreate(
            setting_key="test_setting",
            setting_value="test_value",
            setting_type="string",
            description="Test setting for unit tests",
        )

    def test_create_news_article(self, db_session, sample_article_data):
        """Test creating a news article"""
        result = ContentService.create_news_article(db_session, sample_article_data)

        assert isinstance(result, NewsArticleResponse)
        assert result.title == sample_article_data.title
        assert result.content == sample_article_data.content
        assert result.is_featured == sample_article_data.is_featured
        assert result.is_active == sample_article_data.is_active

    def test_get_news_article(self, db_session, sample_article_data):
        """Test getting a news article by ID"""
        # Create an article first
        created_article = ContentService.create_news_article(
            db_session, sample_article_data
        )

        # Get the article by ID
        result = ContentService.get_news_article(
            db_session, str(created_article.article_id)
        )

        assert isinstance(result, NewsArticleResponse)
        assert result.article_id == created_article.article_id
        assert result.title == sample_article_data.title

    def test_get_news_article_not_found(self, db_session):
        """Test getting a news article that doesn't exist"""
        result = ContentService.get_news_article(db_session, "non-existent-id")
        assert result is None

    def test_create_video(self, db_session, sample_video_data):
        """Test creating a video"""
        result = ContentService.create_video(db_session, sample_video_data)

        assert isinstance(result, VideoResponse)
        assert result.title == sample_video_data.title
        assert result.video_url == sample_video_data.video_url
        assert result.video_type == sample_video_data.video_type

    def test_get_videos_by_type(self, db_session, sample_video_data):
        """Test getting videos by type"""
        # Create a video first
        created_video = ContentService.create_video(db_session, sample_video_data)

        # Get videos by type
        result = ContentService.get_videos_by_type(db_session, "informational", 0, 10)

        assert len(result) == 1
        assert isinstance(result[0], VideoResponse)
        assert result[0].video_id == created_video.video_id

    def test_create_system_setting(self, db_session, sample_setting_data):
        """Test creating a system setting"""
        result = ContentService.create_system_setting(db_session, sample_setting_data)

        assert isinstance(result, SystemSettingResponse)
        assert result.setting_key == sample_setting_data.setting_key
        assert result.setting_value == sample_setting_data.setting_value

    def test_get_setting_value(self, db_session, sample_setting_data):
        """Test getting setting value by key"""
        # Create a setting first
        ContentService.create_system_setting(db_session, sample_setting_data)

        result = ContentService.get_setting_value(db_session, "test_setting")
        assert result == "test_value"

    def test_get_setting_value_not_found(self, db_session):
        """Test getting setting value that doesn't exist"""
        result = ContentService.get_setting_value(db_session, "non_existent_key")
        assert result is None

    def test_get_active_news_articles(self, db_session, sample_article_data):
        """Test getting active news articles"""
        # Create an article
        ContentService.create_news_article(db_session, sample_article_data)

        # Get active articles
        result = ContentService.get_active_news_articles(db_session)

        assert len(result) == 1
        assert isinstance(result[0], NewsArticleResponse)
        assert result[0].is_active == True

    def test_get_featured_news_articles(self, db_session, sample_article_data):
        """Test getting featured news articles"""
        # Create a featured article
        ContentService.create_news_article(db_session, sample_article_data)

        # Get featured articles
        result = ContentService.get_featured_news_articles(db_session)

        assert len(result) == 1
        assert isinstance(result[0], NewsArticleResponse)
        assert result[0].is_featured == True

    def test_get_active_videos(self, db_session, sample_video_data):
        """Test getting active videos"""
        # Create a video
        ContentService.create_video(db_session, sample_video_data)

        # Get active videos
        result = ContentService.get_active_videos(db_session)

        assert len(result) == 1
        assert isinstance(result[0], VideoResponse)
        assert result[0].is_active == True
