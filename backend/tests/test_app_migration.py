"""Tests for database migration functionality in app.py."""
import sqlite3
import tempfile
import os
from unittest.mock import patch

import pytest


def test_migration_adds_missing_columns():
    """Test that the migration adds missing columns to an old schema database."""
    # Create a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Create the old schema directly (without check_detail and error_type)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE servers (
                id INTEGER PRIMARY KEY,
                ip_address VARCHAR(45) NOT NULL,
                port INTEGER DEFAULT 22,
                username VARCHAR(100) NOT NULL,
                encrypted_password TEXT NOT NULL,
                notes TEXT,
                status VARCHAR(20) DEFAULT 'unknown',
                last_checked DATETIME,
                os_info VARCHAR(255),
                cpu_info VARCHAR(255),
                memory_info VARCHAR(255),
                disk_info VARCHAR(255),
                uptime VARCHAR(255),
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')
        # Insert a test server without the new columns
        cursor.execute('''
            INSERT INTO servers (ip_address, username, encrypted_password, status)
            VALUES ('192.168.1.1', 'testuser', 'encrypted_pass', 'unknown')
        ''')
        conn.commit()
        conn.close()
        
        # Test the migration function directly instead of relying on create_app
        from sqlalchemy import create_engine, inspect, text
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Check columns before migration
        inspector = inspect(engine)
        columns_before = {col['name'] for col in inspector.get_columns('servers')}
        assert 'check_detail' not in columns_before, "check_detail should not exist before migration"
        assert 'error_type' not in columns_before, "error_type should not exist before migration"
        
        # Run migration directly
        from app import _migrate_add_missing_columns
        _migrate_add_missing_columns(engine)
        
        # Check columns after migration
        inspector = inspect(engine)
        columns_after = {col['name'] for col in inspector.get_columns('servers')}
        
        assert 'check_detail' in columns_after, "check_detail column should have been added"
        assert 'error_type' in columns_after, "error_type column should have been added"
        
        # Verify existing data is preserved
        with engine.connect() as conn:
            result = conn.execute(text("SELECT ip_address FROM servers WHERE id = 1"))
            row = result.fetchone()
        
        assert row is not None, "Existing data should be preserved"
        assert row[0] == '192.168.1.1', "IP address should be preserved"
        
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_migration_is_idempotent():
    """Test that running migration multiple times doesn't cause errors."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Create a database with the new schema
        from sqlalchemy import create_engine, text
        engine = create_engine(f'sqlite:///{db_path}')
        
        with engine.connect() as conn:
            conn.execute(text('''
                CREATE TABLE servers (
                    id INTEGER PRIMARY KEY,
                    ip_address VARCHAR(45) NOT NULL,
                    check_detail TEXT,
                    error_type VARCHAR(50)
                )
            '''))
            conn.commit()
        
        # Run migration - should not fail even though columns already exist
        from app import _migrate_add_missing_columns
        _migrate_add_missing_columns(engine)
        
        # Run it again - still should not fail
        _migrate_add_missing_columns(engine)
        
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_migration_skips_missing_table():
    """Test that migration doesn't fail when servers table doesn't exist."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Create an empty database (no tables)
        from sqlalchemy import create_engine
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Run migration - should not fail even though table doesn't exist
        from app import _migrate_add_missing_columns
        _migrate_add_missing_columns(engine)  # Should complete without error
        
        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
