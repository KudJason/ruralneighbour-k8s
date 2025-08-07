import pytest
from datetime import date, datetime, timedelta
from app.services.retention_service import RetentionService
from app.schemas.news_article import NewsArticleCreate
from app.schemas.video import VideoCreate, VideoType
from app.services.content_service import ContentService


class TestRetentionService:
    """Unit tests for RetentionService"""

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
            expiry_date=date.today() - timedelta(days=1),  # Expired
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
            expiry_date=date.today() - timedelta(days=1),  # Expired
        )

    def test_get_expired_content(
        self, db_session, sample_article_data, sample_video_data
    ):
        """Test getting expired content"""
        # Create expired content
        ContentService.create_news_article(db_session, sample_article_data)
        ContentService.create_video(db_session, sample_video_data)

        result = RetentionService.get_expired_content(db_session)

        assert "expired_articles" in result
        assert "expired_videos" in result
        assert len(result["expired_articles"]) == 1
        assert len(result["expired_videos"]) == 1

    def test_mark_expired_content_inactive(
        self, db_session, sample_article_data, sample_video_data
    ):
        """Test marking expired content as inactive"""
        # Create expired content
        ContentService.create_news_article(db_session, sample_article_data)
        ContentService.create_video(db_session, sample_video_data)

        result = RetentionService.mark_expired_content_inactive(db_session)

        assert result["articles_marked_inactive"] == 1
        assert result["videos_marked_inactive"] == 1
        assert result["total_content_processed"] == 2

    def test_set_expiry_dates_for_new_content_article(self, db_session):
        """Test setting expiry date for new article"""
        # Create article data without expiry date
        article_data = NewsArticleCreate(
            title="Test Article",
            content="This is a test article content",
            author_id=None,
            image_url="https://example.com/image.jpg",
            is_featured=True,
            is_active=True,
            publish_date=date.today(),
            expiry_date=None,
        )

        # Create the article
        created_article = ContentService.create_news_article(db_session, article_data)

        # Set expiry date
        result = RetentionService.set_expiry_dates_for_new_content(
            db_session, "article", str(created_article.article_id)
        )

        assert result is True

    def test_set_expiry_dates_for_new_content_video(self, db_session):
        """Test setting expiry date for new video"""
        # Create video data without expiry date
        video_data = VideoCreate(
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

        # Create the video
        created_video = ContentService.create_video(db_session, video_data)

        # Set expiry date
        result = RetentionService.set_expiry_dates_for_new_content(
            db_session, "video", str(created_video.video_id)
        )

        assert result is True

    def test_set_expiry_dates_for_new_content_not_found(self, db_session):
        """Test setting expiry date for content that doesn't exist"""
        result = RetentionService.set_expiry_dates_for_new_content(
            db_session, "article", "non-existent-id"
        )

        assert result is False

    def test_get_retention_statistics(
        self, db_session, sample_article_data, sample_video_data
    ):
        """Test getting retention statistics"""
        # Create expired content
        ContentService.create_news_article(db_session, sample_article_data)
        ContentService.create_video(db_session, sample_video_data)

        result = RetentionService.get_retention_statistics(db_session)

        assert "retention_policy_days" in result
        assert "expired_articles_count" in result
        assert "expired_videos_count" in result
        assert "total_expired_content" in result
        assert "last_check" in result

        assert result["expired_articles_count"] == 1
        assert result["expired_videos_count"] == 1
        assert result["total_expired_content"] == 2
