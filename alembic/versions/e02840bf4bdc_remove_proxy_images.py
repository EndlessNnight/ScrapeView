"""remove proxy images

Revision ID: e02840bf4bdc
Revises: 
Create Date: 2025-03-15 17:43:57.780011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'e02840bf4bdc'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_api_logs_id', table_name='api_logs')
    op.drop_table('api_logs')
    op.drop_index('ix_douyin_contents_id', table_name='douyin_contents')
    op.drop_table('douyin_contents')
    op.drop_index('ix_proxy_images_id', table_name='proxy_images')
    op.drop_index('ix_proxy_images_original_url', table_name='proxy_images')
    op.drop_table('proxy_images')
    op.drop_index('ix_douyin_content_files_aweme_id', table_name='douyin_content_files')
    op.drop_index('ix_douyin_content_files_id', table_name='douyin_content_files')
    op.drop_table('douyin_content_files')
    op.drop_index('ix_douyin_creators_id', table_name='douyin_creators')
    op.drop_index('ix_douyin_creators_sec_user_id', table_name='douyin_creators')
    op.drop_table('douyin_creators')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('douyin_creators',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('sec_user_id', sa.VARCHAR(length=100), nullable=False),
    sa.Column('nickname', sa.VARCHAR(length=100), nullable=False),
    sa.Column('avatar_url', sa.TEXT(), nullable=True),
    sa.Column('unique_id', sa.VARCHAR(length=100), nullable=True),
    sa.Column('signature', sa.TEXT(), nullable=True),
    sa.Column('ip_location', sa.VARCHAR(length=100), nullable=True),
    sa.Column('gender', sa.INTEGER(), nullable=True),
    sa.Column('follower_count', sa.BIGINT(), nullable=True),
    sa.Column('following_count', sa.BIGINT(), nullable=True),
    sa.Column('aweme_count', sa.BIGINT(), nullable=True),
    sa.Column('total_favorited', sa.BIGINT(), nullable=True),
    sa.Column('status', sa.INTEGER(), nullable=True),
    sa.Column('auto_update', sa.INTEGER(), nullable=True),
    sa.Column('download_video', sa.INTEGER(), nullable=True),
    sa.Column('download_cover', sa.INTEGER(), nullable=True),
    sa.Column('last_aweme_id', sa.VARCHAR(length=50), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_douyin_creators_sec_user_id', 'douyin_creators', ['sec_user_id'], unique=1)
    op.create_index('ix_douyin_creators_id', 'douyin_creators', ['id'], unique=False)
    op.create_table('douyin_content_files',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('content_id', sa.INTEGER(), nullable=False),
    sa.Column('aweme_id', sa.VARCHAR(length=50), nullable=False),
    sa.Column('file_type', sa.VARCHAR(length=20), nullable=False),
    sa.Column('file_index', sa.INTEGER(), nullable=True),
    sa.Column('file_path', sa.VARCHAR(length=500), nullable=True),
    sa.Column('cover_path', sa.VARCHAR(length=500), nullable=True),
    sa.Column('origin_cover_path', sa.VARCHAR(length=500), nullable=True),
    sa.Column('dynamic_cover_path', sa.VARCHAR(length=500), nullable=True),
    sa.Column('file_size', sa.BIGINT(), nullable=True),
    sa.Column('file_hash', sa.VARCHAR(length=100), nullable=True),
    sa.Column('download_status', sa.VARCHAR(length=20), nullable=True),
    sa.Column('error_message', sa.TEXT(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['content_id'], ['douyin_contents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('aweme_id', 'file_type', 'file_index', name='uix_aweme_id_file_type_index')
    )
    op.create_index('ix_douyin_content_files_id', 'douyin_content_files', ['id'], unique=False)
    op.create_index('ix_douyin_content_files_aweme_id', 'douyin_content_files', ['aweme_id'], unique=False)
    op.create_table('proxy_images',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('original_url', sa.VARCHAR(length=1024), nullable=False),
    sa.Column('local_path', sa.VARCHAR(length=255), nullable=False),
    sa.Column('file_name', sa.VARCHAR(length=255), nullable=False),
    sa.Column('file_size', sa.INTEGER(), nullable=True),
    sa.Column('mime_type', sa.VARCHAR(length=100), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_proxy_images_original_url', 'proxy_images', ['original_url'], unique=False)
    op.create_index('ix_proxy_images_id', 'proxy_images', ['id'], unique=False)
    op.create_table('douyin_contents',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('aweme_id', sa.VARCHAR(length=50), nullable=False),
    sa.Column('creator_id', sa.INTEGER(), nullable=False),
    sa.Column('desc', sa.TEXT(), nullable=True),
    sa.Column('group_id', sa.VARCHAR(length=50), nullable=True),
    sa.Column('create_time', sa.BIGINT(), nullable=True),
    sa.Column('is_top', sa.INTEGER(), nullable=True),
    sa.Column('content_type', sa.VARCHAR(length=20), nullable=False),
    sa.Column('aweme_type', sa.INTEGER(), nullable=True),
    sa.Column('media_type', sa.INTEGER(), nullable=True),
    sa.Column('admire_count', sa.INTEGER(), nullable=True),
    sa.Column('comment_count', sa.INTEGER(), nullable=True),
    sa.Column('digg_count', sa.INTEGER(), nullable=True),
    sa.Column('collect_count', sa.INTEGER(), nullable=True),
    sa.Column('play_count', sa.INTEGER(), nullable=True),
    sa.Column('share_count', sa.INTEGER(), nullable=True),
    sa.Column('duration', sa.INTEGER(), nullable=True),
    sa.Column('video_height', sa.INTEGER(), nullable=True),
    sa.Column('video_width', sa.INTEGER(), nullable=True),
    sa.Column('images_count', sa.INTEGER(), nullable=True),
    sa.Column('image_urls', sqlite.JSON(), nullable=True),
    sa.Column('tags', sqlite.JSON(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['douyin_creators.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('aweme_id')
    )
    op.create_index('ix_douyin_contents_id', 'douyin_contents', ['id'], unique=False)
    op.create_table('api_logs',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('method', sa.VARCHAR(length=10), nullable=False),
    sa.Column('path', sa.VARCHAR(length=255), nullable=False),
    sa.Column('query_params', sa.TEXT(), nullable=True),
    sa.Column('request_body', sa.TEXT(), nullable=True),
    sa.Column('response_body', sa.TEXT(), nullable=True),
    sa.Column('status_code', sa.INTEGER(), nullable=True),
    sa.Column('ip_address', sa.VARCHAR(length=50), nullable=True),
    sa.Column('user_agent', sa.VARCHAR(length=255), nullable=True),
    sa.Column('duration_ms', sa.INTEGER(), nullable=True),
    sa.Column('has_binary_data', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_logs_id', 'api_logs', ['id'], unique=False)
    # ### end Alembic commands ###
