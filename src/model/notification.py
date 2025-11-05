"""
Modelos de Notificações e Lixeira
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from db.database import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    __table_args__ = (
        Index('idx_notifications_user_unread', 'user_id', 'is_read'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class NotificationTrash(db.Model):
    __tablename__ = 'notifications_trash'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # guardamos referência ao id original apenas para auditoria
    original_notification_id = Column(Integer, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime)
    trashed_at = Column(DateTime, default=func.now(), index=True)

    __table_args__ = (
        Index('idx_notifications_trash_user', 'user_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'original_notification_id': self.original_notification_id,
            'user_id': self.user_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'trashed_at': self.trashed_at.isoformat() if self.trashed_at else None,
        }


