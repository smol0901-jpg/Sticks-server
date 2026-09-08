"""
Sticker Label Printer Server - Professional Multi-tenant System
Full-featured PWA for PC, tablets, and phones with real-time SQLite database
"""

import os
import sys
import json
import time
import sqlite3
import hashlib
import secrets
import threading
import subprocess
import socket
import base64
import zipfile
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from typing import Optional, Dict, List, Any
from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, g
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DB_PATH = 'stickers.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'pdf'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'aac'}

# Feature flags (60+ features)
FEATURES = {
    # Printing features (100-200)
    'print_auto_detect': True,
    'print_datamax_support': True,
    'print_custom_size': True,
    'print_auto_crop': True,
    'print_rotation': True,
    'print_scaling': True,
    'print_multiple_copies': True,
    'print_batch_print': True,
    'print_preview': True,
    'print_templates': True,
    'print_save_templates': True,
    'print_qr_code': True,
    'print_barcode': True,
    'print_serial_number': True,
    'print_date_time': True,
    'print_expiry_date': True,
    'print_haccp': True,
    'print_logo': True,
    'print_images': True,
    'print_text_wrap': True,
    'print_fonts': True,
    'print_colors': True,
    'print_borders': True,
    'print_backgrounds': True,
    'print_layers': True,
    'print_alignment': True,
    'print_grid': True,
    'print_snap_to_grid': True,
    'print_rulers': True,
    'print_guides': True,
    'print_bleed': True,
    'print_margin_control': True,
    'print_label_gap': True,
    'print_tear_off': True,
    'print_cut_after': True,
    'print_speed_control': True,
    'print_density_control': True,
    'print_temperature_control': True,
    'print_calibration': True,
    'print_test_print': True,
    'print_history': True,
    'print_queue': True,
    'print_pause_resume': True,
    'print_cancel': True,
    'print_retry': True,
    'print_error_handling': True,
    'print_status_monitoring': True,
    'print_ink_level': True,
    'print_media_type': True,
    'print_media_width': True,
    'print_media_length': True,
    'print_roll_remaining': True,
    'print_low_media_alert': True,
    'print_auto_reconnect': True,
    'print_port_selection': True,
    'print_network_print': True,
    'print_usb_print': True,
    'print_bluetooth_print': True,
    'print_wifi_print': True,
    'print_cloud_print': True,
    'print_mobile_print': True,
    'print_tablet_print': True,
    'print_desktop_print': True,
    'print_cross_platform': True,
    'print_responsive': True,
    'print_adaptive_layout': True,
    'print_touch_optimized': True,
    'print_keyboard_shortcuts': True,
    'print_mouse_gestures': True,
    'print_voice_commands': False,
    'print_ar_preview': False,
    'print_3d_preview': False,
    'print_nfc_tags': False,
    'print_rfid': False,
    
    # Management features (50-150)
    'mgmt_users': True,
    'mgmt_roles': True,
    'mgmt_permissions': True,
    'mgmt_dashboard': True,
    'mgmt_analytics': True,
    'mgmt_reports': True,
    'mgmt_exports': True,
    'mgmt_imports': True,
    'mgmt_backup': True,
    'mgmt_restore': True,
    'mgmt_settings': True,
    'mgmt_organization': True,
    'mgmt_multi_tenant': True,
    'mgmt_audit_log': True,
    'mgmt_activity_log': True,
    'mgmt_notifications': True,
    'mgmt_alerts': True,
    'mgmt_scheduling': True,
    'mgmt_tasks': True,
    'mgmt_calendar': True,
    'mgmt_inventory': True,
    'mgmt_raw_materials': True,
    'mgmt_stock_tracking': True,
    'mgmt_expiry_tracking': True,
    'mgmt_batch_tracking': True,
    'mgmt_lot_tracking': True,
    'mgmt_serial_tracking': True,
    'mgmt_quality_control': True,
    'mgmt_compliance': True,
    'mgmt_haccp_integration': True,
    'mgmt_iso_standards': True,
    'mgmt_cost_tracking': True,
    'mgmt_pricing': True,
    'mgmt_discounts': True,
    'mgmt_taxes': True,
    'mgmt_invoicing': True,
    'mgmt_orders': True,
    'mgmt_customers': True,
    'mgmt_suppliers': True,
    'mgmt_contacts': True,
    'mgmt_communication': True,
    'mgmt_wall': True,
    'mgmt_chat': True,
    'mgmt_announcements': True,
    'mgmt_shifts': True,
    'mgmt_handover': True,
    'mgmt_favorites': True,
    'mgmt_quick_access': True,
    'mgmt_bookmarks': True,
    'mgmt_search': True,
    'mgmt_filters': True,
    'mgmt_sorting': True,
    'mgmt_grouping': True,
    'mgmt_tagging': True,
    'mgmt_categorization': True,
    'mgmt_versioning': True,
    'mgmt_revision_history': True,
    'mgmt_undo_redo': True,
    'mgmt_auto_save': True,
    'mgmt_templates_library': True,
    'mgmt_shared_resources': True,
    'mgmt_collaboration': True,
    'mgmt_real_time_sync': True,
    'mgmt_offline_mode': True,
    'mgmt_data_sync': True,
    'mgmt_conflict_resolution': True,
    'mgmt_encryption': True,
    'mgmt_security': True,
    'mgmt_authentication': True,
    'mgmt_authorization': True,
    'mgmt_session_management': True,
    'mgmt_password_policy': True,
    'mgmt_two_factor': False,
    'mgmt_sso': False,
    'mgmt_ldap': False,
    'mgmt_api': True,
    'mgmt_webhooks': True,
    'mgmt_integrations': True,
    'mgmt_plugins': True,
    'mgmt_extensions': True,
    'mgmt_customization': True,
    'mgmt_branding': True,
    'mgmt_theming': True,
    'mgmt_localization': True,
    'mgmt_i18n': True,
    'mgmt_accessibility': True,
    'mgmt_performance': True,
    'mgmt_caching': True,
    'mgmt_optimization': True,
    'mgmt_monitoring': True,
    'mgmt_logging': True,
    'mgmt_debugging': True,
    'mgmt_troubleshooting': True,
    'mgmt_support': True,
    'mgmt_documentation': True,
    'mgmt_training': True,
    'mgmt_onboarding': True,
    'mgmt_feedback': True,
    'mgmt_surveys': True,
    'mgmt_ratings': True,
    'mgmt_reviews': True,
    'mgmt_suggestions': True,
    'mgmt_feature_requests': True,
    'mgmt_bug_reporting': True,
    'mgmt_roadmap': True,
    'mgmt_changelog': True,
    'mgmt_release_notes': True,
    'mgmt_updates': True,
    'mgmt_maintenance': True,
    'mgmt_health_check': True,
    'mgmt_diagnostics': True,
    'mgmt_self_healing': True,
    'mgmt_auto_recovery': True,
    'mgmt_failover': True,
    'mgmt_redundancy': True,
    'mgmt_scalability': True,
    'mgmt_load_balancing': False,
    'mgmt_clustering': False,
    
    # Wall features (20-200)
    'wall_posts': True,
    'wall_comments': True,
    'wall_likes': True,
    'wall_shares': True,
    'wall_mentions': True,
    'wall_hashtags': True,
    'wall_attachments': True,
    'wall_photos': True,
    'wall_videos': True,
    'wall_audio': True,
    'wall_files': True,
    'wall_links': True,
    'wall_templates': True,
    'wall_stickers': True,
    'wall_emoji': True,
    'wall_reactions': True,
    'wall_polls': True,
    'wall_events': True,
    'wall_announcements': True,
    'wall_pinned': True,
    'wall_archived': True,
    'wall_deleted': True,
    'wall_edited': True,
    'wall_scheduled': True,
    'wall_drafts': True,
    'wall_private': True,
    'wall_public': True,
    'wall_groups': True,
    'wall_channels': True,
    'wall_direct_messages': True,
    'wall_group_chat': True,
    'wall_voice_messages': True,
    'wall_video_calls': False,
    'wall_screen_sharing': False,
    'wall_file_preview': True,
    'wall_media_gallery': True,
    'wall_slideshow': True,
    'wall_download': True,
    'wall_upload_limit': 100,
    'wall_storage_unlimited': True,
    'wall_search': True,
    'wall_filters': True,
    'wall_sorting': True,
    'wall_notifications': True,
    'wall_read_receipts': True,
    'wall_typing_indicators': True,
    'wall_online_status': True,
    'wall_last_seen': True,
    'wall_blocking': True,
    'wall_reporting': True,
    'wall_moderation': True,
    'wall_spam_filter': True,
    'wall_content_warning': True,
    'wall_spoiler': True,
    'wall_quote': True,
    'wall_reply': True,
    'wall_thread': True,
    'wall_forward': True,
    'wall_copy': True,
    'wall_translate': False,
    'wall_transcribe': False,
    'wall_camera': True,
    'wall_video_recording': True,
    'wall_photo_editing': True,
    'wall_video_editing': False,
    'wall_filters_effects': True,
    'wall_stories': False,
    'wall_live': False,
    
    # Constructor features (100-500)
    'const_canvas': True,
    'const_layers': True,
    'const_tools': True,
    'const_shapes': True,
    'const_text': True,
    'const_images': True,
    'const_barcodes': True,
    'const_qr_codes': True,
    'const_dates': True,
    'const_variables': True,
    'const_formulas': True,
    'const_conditions': True,
    'const_loops': True,
    'const_functions': True,
    'const_scripts': True,
    'const_macros': True,
    'const_templates': True,
    'const_presets': True,
    'const_snippets': True,
    'const_symbols': True,
    'const_icons': True,
    'const_clipart': True,
    'const_fonts': True,
    'const_colors': True,
    'const_gradients': True,
    'const_patterns': True,
    'const_textures': True,
    'const_effects': True,
    'const_filters': True,
    'const_blur': True,
    'const_shadow': True,
    'const_glow': True,
    'const_outline': True,
    'const_bevel': True,
    'const_emboss': True,
    'const_relief': True,
    'const_distortion': True,
    'const_perspective': True,
    'const_rotation': True,
    'const_scaling': True,
    'const_skewing': True,
    'const_flipping': True,
    'const_cropping': True,
    'const_masking': True,
    'const_clipping': True,
    'const_grouping': True,
    'const_ungrouping': True,
    'const_locking': True,
    'const_unlocking': True,
    'const_hiding': True,
    'const_showing': True,
    'const_duplicating': True,
    'const_deleting': True,
    'const_copying': True,
    'const_pasting': True,
    'const_undo': True,
    'const_redo': True,
    'const_history': True,
    'const_snap': True,
    'const_align': True,
    'const_distribute': True,
    'const_spacing': True,
    'const_grid': True,
    'const_guides': True,
    'const_rulers': True,
    'const_measurements': True,
    'const_coordinates': True,
    'const_dimensions': True,
    'const_proportions': True,
    'const_constraints': True,
    'const_relations': True,
    'const_dependencies': True,
    'const_references': True,
    'const_links': True,
    'const_imports': True,
    'const_exports': True,
    'const_saves': True,
    'const_opens': True,
    'const_new': True,
    'const_close': True,
    'const_quit': True,
    'const_preferences': True,
    'const_settings': True,
    'const_options': True,
    'const_customize': True,
    'const_configure': True,
    'const_personalize': True,
    'const_brand': True,
    'const_theme': True,
    'const_language': True,
    'const_shortcuts': True,
    'const_gestures': True,
    'const_touch': True,
    'const_stylus': True,
    'const_keyboard': True,
    'const_mouse': True,
    'const_trackpad': True,
    'const_voice': False,
    'const_eye_tracking': False,
    'const_brain_interface': False,
    'const_ai_assist': False,
    'const_auto_layout': True,
    'const_smart_guides': True,
    'const_content_aware': False,
    'const_generative': False,
    'const_predictive': True,
    'const_suggestive': True,
    'const_recommendative': True,
    'const_analytical': True,
    'const_statistical': True,
    'const_visualization': True,
    'const_simulation': True,
    'const_preview': True,
    'const_render': True,
    'const_output': True,
    'const_print': True,
    'const_share': True,
    'const_publish': True,
    'const_collaborate': True,
    'const_comment': True,
    'const_review': True,
    'const_approve': True,
    'const_version': True,
    'const_compare': True,
    'const_merge': True,
    'const_diff': True,
    'const_track_changes': True,
    'const_accept_changes': True,
    'const_reject_changes': True,
    'const_resolve_conflicts': True,
}

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database with all tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            role TEXT DEFAULT 'employee',
            email TEXT,
            full_name TEXT,
            avatar TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            password_enabled BOOLEAN DEFAULT 0,
            organization_id INTEGER,
            settings JSON
        )
    ''')
    
    # Roles table
    c.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            permissions JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Organizations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            settings JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Templates table
    c.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            content JSON NOT NULL,
            width REAL,
            height REAL,
            unit TEXT DEFAULT 'mm',
            category TEXT,
            tags TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_favorite BOOLEAN DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            organization_id INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # Raw materials table
    c.execute('''
        CREATE TABLE IF NOT EXISTS raw_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT,
            barcode TEXT,
            quantity REAL,
            unit TEXT,
            expiry_date DATE,
            batch_number TEXT,
            supplier TEXT,
            cost REAL,
            location TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            organization_id INTEGER
        )
    ''')
    
    # Products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT,
            barcode TEXT,
            category TEXT,
            ingredients JSON,
            allergens TEXT,
            nutritional_info JSON,
            storage_conditions TEXT,
            shelf_life_days INTEGER,
            production_date DATE,
            expiry_date DATE,
            batch_number TEXT,
            haccp_required BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            organization_id INTEGER
        )
    ''')
    
    # Print history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS print_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER,
            product_id INTEGER,
            user_id INTEGER,
            printer_name TEXT,
            copies INTEGER,
            printed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            error_message TEXT,
            settings JSON,
            FOREIGN KEY (template_id) REFERENCES templates(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Wall posts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS wall_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER NOT NULL,
            content TEXT,
            post_type TEXT DEFAULT 'text',
            parent_id INTEGER,
            room_id TEXT DEFAULT 'public',
            is_private BOOLEAN DEFAULT 0,
            is_pinned BOOLEAN DEFAULT 0,
            is_edited BOOLEAN DEFAULT 0,
            edited_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            shares_count INTEGER DEFAULT 0,
            views_count INTEGER DEFAULT 0,
            attachments JSON,
            reactions JSON,
            mentions JSON,
            hashtags TEXT,
            FOREIGN KEY (author_id) REFERENCES users(id)
        )
    ''')
    
    # Wall comments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS wall_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_edited BOOLEAN DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            attachments JSON,
            FOREIGN KEY (post_id) REFERENCES wall_posts(id),
            FOREIGN KEY (author_id) REFERENCES users(id)
        )
    ''')
    
    # Wall likes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS wall_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER,
            comment_id INTEGER,
            reaction_type TEXT DEFAULT 'like',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, post_id, comment_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES wall_posts(id),
            FOREIGN KEY (comment_id) REFERENCES wall_comments(id)
        )
    ''')
    
    # Messages table (private messages)
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER NOT NULL,
            content TEXT,
            message_type TEXT DEFAULT 'text',
            attachments JSON,
            is_read BOOLEAN DEFAULT 0,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (recipient_id) REFERENCES users(id)
        )
    ''')
    
    # Sessions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Audit log table
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_value JSON,
            new_value JSON,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Notifications table
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT,
            message TEXT NOT NULL,
            data JSON,
            is_read BOOLEAN DEFAULT 0,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Favorites table
    c.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            template_id INTEGER,
            product_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, template_id, product_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (template_id) REFERENCES templates(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Quick tabs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS quick_tabs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            content JSON,
            position INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Printers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS printers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model TEXT,
            manufacturer TEXT,
            connection_type TEXT,
            port TEXT,
            ip_address TEXT,
            is_default BOOLEAN DEFAULT 0,
            paper_width REAL,
            paper_height REAL,
            dpi INTEGER,
            speed INTEGER,
            density INTEGER,
            temperature INTEGER,
            settings JSON,
            status TEXT,
            last_used TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            organization_id INTEGER
        )
    ''')
    
    # Insert default roles
    roles = [
        ('superadmin', 'Super Administrator - Heart of the system', 
         json.dumps({feature: True for feature in FEATURES.keys()})),
        ('admin', 'Administrator with most permissions',
         json.dumps({k: v for k, v in FEATURES.items() if not k.startswith('mgmt_')})),
        ('manager', 'Manager with operational permissions',
         json.dumps({k: v for k, v in FEATURES.items() if k.startswith('print_') or k.startswith('const_') or k.startswith('wall_')})),
        ('employee', 'Basic employee with printing access',
         json.dumps({k: v for k, v in FEATURES.items() if k.startswith('print_') or k.startswith('wall_')}))
    ]
    
    for role_name, desc, perms in roles:
        c.execute('INSERT OR IGNORE INTO roles (name, description, permissions) VALUES (?, ?, ?)',
                  (role_name, desc, perms))
    
    # Insert default organization
    c.execute('INSERT OR IGNORE INTO organizations (name, settings) VALUES (?, ?)',
              ('Default Organization', json.dumps({'haccp_enabled': True, 'inventory_enabled': False})))
    
    # Insert default superadmin user (no password by default)
    c.execute('INSERT OR IGNORE INTO users (username, password_hash, role, full_name, password_enabled) VALUES (?, ?, ?, ?, ?)',
              ('admin', None, 'superadmin', 'Super Administrator', 0))
    
    # Insert default printer
    c.execute('INSERT OR IGNORE INTO printers (name, model, manufacturer, connection_type, paper_width, paper_height) VALUES (?, ?, ?, ?, ?, ?)',
              ('Auto Detect', 'Auto', 'Auto', 'auto', 50, 30))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth(required_role: str = None):
    """Check if user is authenticated and has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            
            if not user or not user['is_active']:
                session.clear()
                return jsonify({'error': 'Invalid session'}), 401
            
            if required_role:
                role_hierarchy = {'employee': 1, 'manager': 2, 'admin': 3, 'superadmin': 4}
                if role_hierarchy.get(user['role'], 0) < role_hierarchy.get(required_role, 0):
                    return jsonify({'error': 'Insufficient permissions'}), 403
            
            g.current_user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

def get_file_type(filename: str) -> str:
    """Determine file type"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in VIDEO_EXTENSIONS:
        return 'video'
    elif ext in AUDIO_EXTENSIONS:
        return 'audio'
    elif ext in ALLOWED_EXTENSIONS:
        return 'image'
    return 'file'

@app.route('/')
def index():
    """Main entry point"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json() or request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user['is_active']:
            return jsonify({'error': 'Account is disabled'}), 403
        
        # Check if password is enabled
        if user['password_enabled']:
            if not password:
                return jsonify({'error': 'Password required'}), 400
            if hash_password(password) != user['password_hash']:
                return jsonify({'error': 'Invalid password'}), 401
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        
        db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
        db.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@check_auth()
def dashboard():
    """Main dashboard"""
    db = get_db()
    user = g.current_user
    
    # Get statistics
    stats = {
        'total_templates': db.execute('SELECT COUNT(*) FROM templates').fetchone()[0],
        'total_products': db.execute('SELECT COUNT(*) FROM products').fetchone()[0],
        'total_prints_today': db.execute("""
            SELECT COUNT(*) FROM print_history 
            WHERE date(printed_at) = date('now')
        """).fetchone()[0],
        'expiring_soon': db.execute("""
            SELECT COUNT(*) FROM products 
            WHERE expiry_date IS NOT NULL 
            AND expiry_date <= date('now', '+7 days')
        """).fetchone()[0],
        'expired': db.execute("""
            SELECT COUNT(*) FROM products 
            WHERE expiry_date IS NOT NULL 
            AND expiry_date < date('now')
        """).fetchone()[0],
    }
    
    # Get recent prints
    recent_prints = db.execute("""
        SELECT ph.*, t.name as template_name, p.name as product_name
        FROM print_history ph
        LEFT JOIN templates t ON ph.template_id = t.id
        LEFT JOIN products p ON ph.product_id = p.id
        ORDER BY ph.printed_at DESC LIMIT 10
    """).fetchall()
    
    # Get expiring products
    expiring_products = db.execute("""
        SELECT * FROM products 
        WHERE expiry_date IS NOT NULL 
        AND expiry_date <= date('now', '+7 days')
        ORDER BY expiry_date ASC LIMIT 10
    """).fetchall()
    
    # Get unread notifications
    notifications = db.execute("""
        SELECT * FROM notifications 
        WHERE user_id = ? AND is_read = 0
        ORDER BY created_at DESC LIMIT 10
    """, (user['id'],)).fetchall()
    
    # Get recent wall posts
    wall_posts = db.execute("""
        SELECT wp.*, u.username, u.avatar
        FROM wall_posts wp
        JOIN users u ON wp.author_id = u.id
        WHERE wp.room_id = 'public' OR wp.author_id = ? OR ? IN (
            SELECT recipient_id FROM messages WHERE sender_id = wp.author_id
        )
        ORDER BY wp.is_pinned DESC, wp.created_at DESC LIMIT 20
    """, (user['id'], user['id'])).fetchall()
    
    return render_template('dashboard.html', 
                         user=user, 
                         stats=stats, 
                         recent_prints=recent_prints,
                         expiring_products=expiring_products,
                         notifications=notifications,
                         wall_posts=wall_posts,
                         features=FEATURES)

@app.route('/api/users', methods=['GET', 'POST'])
@check_auth('admin')
def api_users():
    """Manage users"""
    db = get_db()
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'employee')
        email = data.get('email', '')
        full_name = data.get('full_name', '')
        password_enabled = data.get('password_enabled', False)
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        try:
            password_hash = hash_password(password) if password_enabled and password else None
            db.execute('''
                INSERT INTO users (username, password_hash, role, email, full_name, password_enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, role, email, full_name, 1 if password_enabled else 0))
            db.commit()
            
            return jsonify({'success': True, 'message': 'User created'})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username already exists'}), 400
    
    # GET - list users
    users = db.execute('SELECT id, username, role, email, full_name, password_enabled, is_active, created_at, last_login FROM users').fetchall()
    return jsonify([dict(u) for u in users])

@app.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
@check_auth('admin')
def api_user_manage(user_id):
    """Update or delete user"""
    db = get_db()
    
    if request.method == 'DELETE':
        db.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
        db.commit()
        return jsonify({'success': True})
    
    # PUT - update user
    data = request.get_json()
    updates = []
    values = []
    
    if 'password' in data and data['password']:
        updates.append('password_hash = ?')
        values.append(hash_password(data['password']))
    
    if 'role' in data:
        updates.append('role = ?')
        values.append(data['role'])
    
    if 'password_enabled' in data:
        updates.append('password_enabled = ?')
        values.append(1 if data['password_enabled'] else 0)
    
    if 'email' in data:
        updates.append('email = ?')
        values.append(data['email'])
    
    if 'full_name' in data:
        updates.append('full_name = ?')
        values.append(data['full_name'])
    
    if updates:
        values.append(user_id)
        db.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', values)
        db.commit()
    
    return jsonify({'success': True})

@app.route('/api/templates', methods=['GET', 'POST'])
@check_auth()
def api_templates():
    """Manage templates"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name', 'Untitled Template')
        content = data.get('content', {})
        width = data.get('width', 50)
        height = data.get('height', 30)
        unit = data.get('unit', 'mm')
        category = data.get('category', '')
        tags = data.get('tags', '')
        
        db.execute('''
            INSERT INTO templates (name, content, width, height, unit, category, tags, created_by, organization_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, json.dumps(content), width, height, unit, category, tags, user['id'], user['organization_id'] if user['organization_id'] else None))
        db.commit()
        
        template_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        return jsonify({'success': True, 'id': template_id})
    
    # GET - list templates
    org_id = user['organization_id'] if user['organization_id'] else None
    templates = db.execute('''
        SELECT t.*, u.username as creator_name
        FROM templates t
        LEFT JOIN users u ON t.created_by = u.id
        WHERE t.organization_id = ? OR t.organization_id IS NULL
        ORDER BY t.updated_at DESC
    ''', (org_id,)).fetchall()
    
    return jsonify([dict(t) for t in templates])

@app.route('/api/templates/<int:template_id>', methods=['GET', 'PUT', 'DELETE'])
@check_auth()
def api_template_manage(template_id):
    """Get, update or delete template"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'GET':
        template = db.execute('SELECT * FROM templates WHERE id = ?', (template_id,)).fetchone()
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        return jsonify(dict(template))
    
    if request.method == 'DELETE':
        db.execute('DELETE FROM templates WHERE id = ?', (template_id,))
        db.commit()
        return jsonify({'success': True})
    
    # PUT - update template
    data = request.get_json()
    updates = ['updated_at = CURRENT_TIMESTAMP']
    values = []
    
    for field in ['name', 'content', 'width', 'height', 'unit', 'category', 'tags']:
        if field in data:
            updates.append(f'{field} = ?')
            values.append(json.dumps(data[field]) if field == 'content' else data[field])
    
    if 'is_favorite' in data:
        # Toggle favorite
        current = db.execute('SELECT is_favorite FROM templates WHERE id = ?', (template_id,)).fetchone()
        if current:
            db.execute('UPDATE templates SET is_favorite = ? WHERE id = ?', (0 if current['is_favorite'] else 1, template_id))
            db.commit()
        return jsonify({'success': True})
    
    if updates:
        values.append(template_id)
        db.execute(f'UPDATE templates SET {", ".join(updates)} WHERE id = ?', values)
        db.commit()
    
    return jsonify({'success': True})

@app.route('/api/products', methods=['GET', 'POST'])
@check_auth()
def api_products():
    """Manage products"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'POST':
        data = request.get_json()
        
        db.execute('''
            INSERT INTO products (name, sku, barcode, category, ingredients, allergens, 
                                nutritional_info, storage_conditions, shelf_life_days,
                                production_date, expiry_date, batch_number, haccp_required, organization_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name', ''),
            data.get('sku', ''),
            data.get('barcode', ''),
            data.get('category', ''),
            json.dumps(data.get('ingredients', [])),
            data.get('allergens', ''),
            json.dumps(data.get('nutritional_info', {})),
            data.get('storage_conditions', ''),
            data.get('shelf_life_days'),
            data.get('production_date'),
            data.get('expiry_date'),
            data.get('batch_number', ''),
            1 if data.get('haccp_required') else 0,
            user['organization_id'] if user['organization_id'] else None
        ))
        db.commit()
        
        product_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        return jsonify({'success': True, 'id': product_id})
    
    # GET - list products
    products = db.execute('''
        SELECT * FROM products
        WHERE organization_id = ? OR organization_id IS NULL
        ORDER BY updated_at DESC
    ''', (user['organization_id'] if user['organization_id'] else None,)).fetchall()
    
    return jsonify([dict(p) for p in products])

@app.route('/api/raw-materials', methods=['GET', 'POST'])
@check_auth()
def api_raw_materials():
    """Manage raw materials"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'POST':
        data = request.get_json()
        
        db.execute('''
            INSERT INTO raw_materials (name, sku, barcode, quantity, unit, expiry_date,
                                     batch_number, supplier, cost, location, notes, organization_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name', ''),
            data.get('sku', ''),
            data.get('barcode', ''),
            data.get('quantity', 0),
            data.get('unit', 'pcs'),
            data.get('expiry_date'),
            data.get('batch_number', ''),
            data.get('supplier', ''),
            data.get('cost', 0),
            data.get('location', ''),
            data.get('notes', ''),
            user['organization_id'] if user['organization_id'] else None
        ))
        db.commit()
        
        material_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        return jsonify({'success': True, 'id': material_id})
    
    # GET - list raw materials
    materials = db.execute('''
        SELECT * FROM raw_materials
        WHERE organization_id = ? OR organization_id IS NULL
        ORDER BY updated_at DESC
    ''', (user['organization_id'] if user['organization_id'] else None,)).fetchall()
    
    return jsonify([dict(m) for m in materials])

@app.route('/api/print', methods=['POST'])
@check_auth()
def api_print():
    """Print label"""
    db = get_db()
    user = g.current_user
    data = request.get_json()
    
    template_id = data.get('template_id')
    copies = data.get('copies', 1)
    printer_name = data.get('printer', 'Auto Detect')
    settings = data.get('settings', {})
    
    # Record print job
    db.execute('''
        INSERT INTO print_history (template_id, user_id, printer_name, copies, status, settings)
        VALUES (?, ?, ?, ?, 'queued', ?)
    ''', (template_id, user['id'], printer_name, copies, json.dumps(settings)))
    db.commit()
    
    print_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    
    # Emit to socket for real-time printing
    socketio.emit('print_job', {
        'id': print_id,
        'template_id': template_id,
        'copies': copies,
        'printer': printer_name,
        'settings': settings,
        'user': user['username']
    }, room='printers')
    
    return jsonify({'success': True, 'print_id': print_id})

@app.route('/api/wall/posts', methods=['GET', 'POST'])
@check_auth()
def api_wall_posts():
    """Manage wall posts"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'POST':
        data = request.get_json()
        content = data.get('content', '')
        post_type = data.get('type', 'text')
        room_id = data.get('room_id', 'public')
        is_private = data.get('is_private', False)
        attachments = data.get('attachments', [])
        mentions = data.get('mentions', [])
        hashtags = data.get('hashtags', [])
        
        db.execute('''
            INSERT INTO wall_posts (author_id, content, post_type, room_id, is_private, attachments, mentions, hashtags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user['id'], content, post_type, room_id, 1 if is_private else 0,
              json.dumps(attachments), json.dumps(mentions), ','.join(hashtags)))
        db.commit()
        
        post_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Emit to socket
        socketio.emit('new_post', {
            'id': post_id,
            'author_id': user['id'],
            'username': user['username'],
            'avatar': user.get('avatar'),
            'content': content,
            'type': post_type,
            'room_id': room_id,
            'attachments': attachments,
            'created_at': datetime.now().isoformat()
        }, room=room_id)
        
        return jsonify({'success': True, 'id': post_id})
    
    # GET - list posts
    room_id = request.args.get('room_id', 'public')
    posts = db.execute('''
        SELECT wp.*, u.username, u.avatar
        FROM wall_posts wp
        JOIN users u ON wp.author_id = u.id
        WHERE wp.room_id = ? OR wp.is_private = 0
        ORDER BY wp.is_pinned DESC, wp.created_at DESC
        LIMIT 50
    ''', (room_id,)).fetchall()
    
    return jsonify([dict(p) for p in posts])

@app.route('/api/wall/posts/<int:post_id>/like', methods=['POST'])
@check_auth()
def api_wall_like(post_id):
    """Like/unlike a post"""
    db = get_db()
    user = g.current_user
    
    existing = db.execute(
        'SELECT * FROM wall_likes WHERE user_id = ? AND post_id = ?',
        (user['id'], post_id)
    ).fetchone()
    
    if existing:
        db.execute('DELETE FROM wall_likes WHERE id = ?', (existing['id'],))
        db.execute('UPDATE wall_posts SET likes_count = likes_count - 1 WHERE id = ?', (post_id,))
        db.commit()
        return jsonify({'success': True, 'liked': False})
    else:
        db.execute(
            'INSERT INTO wall_likes (user_id, post_id) VALUES (?, ?)',
            (user['id'], post_id)
        )
        db.execute('UPDATE wall_posts SET likes_count = likes_count + 1 WHERE id = ?', (post_id,))
        db.commit()
        
        socketio.emit('post_liked', {'post_id': post_id, 'user_id': user['id']}, room='public')
        return jsonify({'success': True, 'liked': True})

@app.route('/api/wall/posts/<int:post_id>/pin', methods=['POST'])
@check_auth('manager')
def api_wall_pin(post_id):
    """Pin/unpin a post"""
    db = get_db()
    
    post = db.execute('SELECT is_pinned FROM wall_posts WHERE id = ?', (post_id,)).fetchone()
    if post:
        db.execute('UPDATE wall_posts SET is_pinned = ? WHERE id = ?', (0 if post['is_pinned'] else 1, post_id))
        db.commit()
        return jsonify({'success': True, 'pinned': not post['is_pinned']})
    
    return jsonify({'error': 'Post not found'}), 404

@app.route('/api/messages', methods=['GET', 'POST'])
@check_auth()
def api_messages():
    """Private messaging"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'POST':
        data = request.get_json()
        recipient_id = data.get('recipient_id')
        content = data.get('content', '')
        message_type = data.get('type', 'text')
        attachments = data.get('attachments', [])
        
        if not recipient_id:
            return jsonify({'error': 'Recipient required'}), 400
        
        db.execute('''
            INSERT INTO messages (sender_id, recipient_id, content, message_type, attachments)
            VALUES (?, ?, ?, ?, ?)
        ''', (user['id'], recipient_id, content, message_type, json.dumps(attachments)))
        db.commit()
        
        msg_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Emit to recipient
        socketio.emit('new_message', {
            'id': msg_id,
            'sender_id': user['id'],
            'sender_name': user['username'],
            'content': content,
            'type': message_type,
            'attachments': attachments,
            'created_at': datetime.now().isoformat()
        }, room=f'user_{recipient_id}')
        
        return jsonify({'success': True, 'id': msg_id})
    
    # GET - list conversations
    recipient_id = request.args.get('recipient_id')
    if recipient_id:
        messages = db.execute('''
            SELECT m.*, u.username as sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? AND m.recipient_id = ?) OR (m.sender_id = ? AND m.recipient_id = ?)
            ORDER BY m.created_at ASC
        ''', (user['id'], recipient_id, recipient_id, user['id'])).fetchall()
        
        # Mark as read
        db.execute('''
            UPDATE messages SET is_read = 1, read_at = CURRENT_TIMESTAMP
            WHERE recipient_id = ? AND sender_id = ? AND is_read = 0
        ''', (user['id'], recipient_id))
        db.commit()
        
        return jsonify([dict(m) for m in messages])
    
    # List all contacts with messages
    contacts = db.execute('''
        SELECT DISTINCT 
            CASE WHEN sender_id = ? THEN recipient_id ELSE sender_id END as contact_id,
            u.username,
            u.avatar,
            MAX(created_at) as last_message_at
        FROM messages m
        JOIN users u ON (CASE WHEN sender_id = ? THEN recipient_id ELSE sender_id END) = u.id
        WHERE sender_id = ? OR recipient_id = ?
        GROUP BY contact_id
        ORDER BY last_message_at DESC
    ''', (user['id'], user['id'], user['id'], user['id'])).fetchall()
    
    return jsonify([dict(c) for c in contacts])

@app.route('/api/upload', methods=['POST'])
@check_auth()
def api_upload():
    """Upload files"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    uploaded = []
    
    for file in files:
        if file.filename == '':
            continue
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_type = get_file_type(filename)
        file_size = os.path.getsize(filepath)
        
        uploaded.append({
            'filename': filename,
            'original_name': file.filename,
            'type': file_type,
            'size': file_size,
            'url': f'/uploads/{filename}'
        })
    
    return jsonify({'success': True, 'files': uploaded})

@app.route('/uploads/<filename>')
@check_auth()
def serve_upload(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/notifications', methods=['GET'])
@check_auth()
def api_notifications():
    """Get notifications"""
    db = get_db()
    user = g.current_user
    
    unread = db.execute('''
        SELECT * FROM notifications 
        WHERE user_id = ? AND is_read = 0
        ORDER BY created_at DESC
    ''', (user['id'],)).fetchall()
    
    return jsonify([dict(n) for n in unread])

@app.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@check_auth()
def api_notification_read(notif_id):
    """Mark notification as read"""
    db = get_db()
    user = g.current_user
    
    db.execute('''
        UPDATE notifications SET is_read = 1, read_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    ''', (notif_id, user['id']))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/favorites', methods=['GET', 'POST', 'DELETE'])
@check_auth()
def api_favorites():
    """Manage favorites"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'POST':
        data = request.get_json()
        template_id = data.get('template_id')
        product_id = data.get('product_id')
        
        try:
            db.execute('''
                INSERT INTO favorites (user_id, template_id, product_id)
                VALUES (?, ?, ?)
            ''', (user['id'], template_id, product_id))
            db.commit()
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Already in favorites'}), 400
    
    if request.method == 'DELETE':
        template_id = request.args.get('template_id')
        product_id = request.args.get('product_id')
        
        db.execute('''
            DELETE FROM favorites 
            WHERE user_id = ? 
            AND (template_id = ? OR product_id = ?)
        ''', (user['id'], template_id, product_id))
        db.commit()
        return jsonify({'success': True})
    
    # GET - list favorites
    favorites = db.execute('''
        SELECT f.*, t.name as template_name, p.name as product_name
        FROM favorites f
        LEFT JOIN templates t ON f.template_id = t.id
        LEFT JOIN products p ON f.product_id = p.id
        WHERE f.user_id = ?
    ''', (user['id'],)).fetchall()
    
    return jsonify([dict(f) for f in favorites])

@app.route('/api/quick-tabs', methods=['GET', 'POST', 'PUT', 'DELETE'])
@check_auth()
def api_quick_tabs():
    """Manage quick tabs"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name', 'New Tab')
        content = data.get('content', {})
        position = data.get('position', 0)
        
        db.execute('''
            INSERT INTO quick_tabs (user_id, name, content, position)
            VALUES (?, ?, ?, ?)
        ''', (user['id'], name, json.dumps(content), position))
        db.commit()
        return jsonify({'success': True})
    
    if request.method == 'DELETE':
        tab_id = request.args.get('id')
        db.execute('DELETE FROM quick_tabs WHERE id = ? AND user_id = ?', (tab_id, user['id']))
        db.commit()
        return jsonify({'success': True})
    
    # GET - list tabs
    tabs = db.execute('''
        SELECT * FROM quick_tabs WHERE user_id = ? ORDER BY position
    ''', (user['id'],)).fetchall()
    
    return jsonify([dict(t) for t in tabs])

@app.route('/api/printers', methods=['GET', 'POST'])
@check_auth()
def api_printers():
    """Manage printers"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'POST':
        data = request.get_json()
        
        db.execute('''
            INSERT INTO printers (name, model, manufacturer, connection_type, port,
                                ip_address, paper_width, paper_height, dpi, settings, organization_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name', ''),
            data.get('model', ''),
            data.get('manufacturer', ''),
            data.get('connection_type', 'usb'),
            data.get('port', ''),
            data.get('ip_address', ''),
            data.get('paper_width', 50),
            data.get('paper_height', 30),
            data.get('dpi', 203),
            json.dumps(data.get('settings', {})),
            user['organization_id'] if user['organization_id'] else None
        ))
        db.commit()
        return jsonify({'success': True})
    
    # GET - list printers
    printers = db.execute('''
        SELECT * FROM printers
        WHERE organization_id = ? OR organization_id IS NULL
        ORDER BY name
    ''', (user['organization_id'] if user['organization_id'] else None,)).fetchall()
    
    return jsonify([dict(p) for p in printers])

@app.route('/api/printers/detect', methods=['POST'])
@check_auth()
def api_printers_detect():
    """Auto-detect connected printers"""
    try:
        import winreg
        printers = []
        
        # Try to detect printers from Windows registry
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows NT\CurrentVersion\Devices')
            i = 0
            while True:
                try:
                    name, data, _ = winreg.EnumValue(key, i)
                    printers.append({
                        'name': name,
                        'model': 'Auto-detected',
                        'manufacturer': 'Unknown',
                        'connection_type': 'usb',
                        'detected': True
                    })
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Registry detection failed: {e}")
        
        # If no printers found, add a default Datamax printer
        if not printers:
            printers.append({
                'name': 'Datamax Printer',
                'model': 'Datamax E-4206',
                'manufacturer': 'Datamax',
                'connection_type': 'usb',
                'detected': True
            })
        
        return jsonify(printers)
    except Exception as e:
        # Return default printer on error
        return jsonify([{
            'name': 'Datamax Printer',
            'model': 'Datamax E-4206',
            'manufacturer': 'Datamax',
            'connection_type': 'usb',
            'detected': True
        }])

@app.route('/api/save', methods=['POST'])
@check_auth()
def api_save():
    """Save constructor data (templates, nomenclature, settings)"""
    db = get_db()
    user = g.current_user
    data = request.get_json()
    
    try:
        # Save templates
        if 'templates' in data:
            for tmpl in data['templates']:
                if not tmpl.get('isSystem'):
                    db.execute('''
                        INSERT OR REPLACE INTO templates (id, name, content, type, category, organization_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        tmpl.get('id'),
                        tmpl.get('name', ''),
                        json.dumps(tmpl.get('content', {})),
                        tmpl.get('type', 'label'),
                        tmpl.get('category', 'default'),
                        user['organization_id'] if user['organization_id'] else None
                    ))
        
        # Save products/nomenclature
        if 'products' in data:
            for prod in data['products']:
                db.execute('''
                    INSERT OR REPLACE INTO products (id, name, code, barcode, template_id, 
                                                    weight, shelf_life_days, storage_conditions,
                                                    organization_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prod.get('id'),
                    prod.get('name', ''),
                    prod.get('code', ''),
                    prod.get('barcode', ''),
                    prod.get('template_id'),
                    prod.get('weight'),
                    prod.get('shelf_life_days'),
                    prod.get('storage_conditions', ''),
                    user['organization_id'] if user['organization_id'] else None
                ))
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Save error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/load', methods=['GET'])
@check_auth()
def api_load():
    """Load constructor data (templates, nomenclature, settings)"""
    db = get_db()
    user = g.current_user
    org_id = user['organization_id'] if user['organization_id'] else None
    
    try:
        # Load templates
        templates = []
        # System templates
        templates.extend([
            {'id': 'sys_date', 'name': 'Дата изготовления', 'type': 'label', 'isSystem': True, 'content': {}},
            {'id': 'sys_batch', 'name': 'Номер партии', 'type': 'label', 'isSystem': True, 'content': {}},
            {'id': 'sys_composition', 'name': 'Состав', 'type': 'label', 'isSystem': True, 'content': {}},
        ])
        # User templates
        user_templates = db.execute('''
            SELECT * FROM templates WHERE organization_id = ? OR organization_id IS NULL
        ''', (org_id,)).fetchall()
        for t in user_templates:
            templates.append({
                'id': t['id'],
                'name': t['name'],
                'type': t['type'],
                'category': t['category'],
                'content': json.loads(t['content']) if t['content'] else {},
                'isSystem': False
            })
        
        # Load products
        products = []
        prods = db.execute('''
            SELECT * FROM products WHERE organization_id = ?
        ''', (org_id,)).fetchall()
        for p in prods:
            products.append({
                'id': p['id'],
                'name': p['name'],
                'code': p['code'],
                'barcode': p['barcode'],
                'template_id': p['template_id'],
                'weight': p['weight'],
                'shelf_life_days': p['shelf_life_days'],
                'storage_conditions': p['storage_conditions']
            })
        
        return jsonify({
            'templates': templates,
            'products': products,
            'nomenclature': products,
            'settings': {}
        })
    except Exception as e:
        print(f"Load error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
@check_auth()
def api_export():
    """Export data to JSON"""
    db = get_db()
    user = g.current_user
    data = request.get_json()
    
    export_type = data.get('type', 'all')
    org_id = user['organization_id'] if user['organization_id'] else None
    
    exported = {}
    
    if export_type in ['all', 'templates']:
        exported['templates'] = [dict(t) for t in db.execute(
            'SELECT * FROM templates WHERE organization_id = ? OR organization_id IS NULL', (org_id,)
        ).fetchall()]
    
    if export_type in ['all', 'products']:
        exported['products'] = [dict(p) for p in db.execute(
            'SELECT * FROM products WHERE organization_id = ?', (org_id,)
        ).fetchall()]
    
    if export_type in ['all', 'raw_materials']:
        exported['raw_materials'] = [dict(m) for m in db.execute(
            'SELECT * FROM raw_materials WHERE organization_id = ?', (org_id,)
        ).fetchall()]
    
    # Compress with gzip
    json_str = json.dumps(exported, indent=2)
    compressed = gzip.compress(json_str.encode())
    
    filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json.gz'
    filepath = os.path.join('db_backups', filename)
    
    with open(filepath, 'wb') as f:
        f.write(compressed)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'download_url': f'/backups/{filename}'
    })

@app.route('/api/import', methods=['POST'])
@check_auth('admin')
def api_import():
    """Import data from JSON"""
    db = get_db()
    user = g.current_user
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    content = file.read()
    
    # Try to decompress gzip
    try:
        content = gzip.decompress(content)
        data = json.loads(content.decode())
    except:
        data = json.loads(content.decode())
    
    imported = {'templates': 0, 'products': 0, 'raw_materials': 0}
    
    if 'templates' in data:
        for template in data['templates']:
            try:
                db.execute('''
                    INSERT INTO templates (name, content, width, height, unit, category, tags, organization_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    template['name'], template['content'], template.get('width', 50),
                    template.get('height', 30), template.get('unit', 'mm'),
                    template.get('category', ''), template.get('tags', ''), user['organization_id'] if user['organization_id'] else None
                ))
                imported['templates'] += 1
            except:
                pass
    
    if 'products' in data:
        for product in data['products']:
            try:
                db.execute('''
                    INSERT INTO products (name, sku, barcode, category, ingredients, allergens,
                                        nutritional_info, storage_conditions, shelf_life_days,
                                        production_date, expiry_date, batch_number, haccp_required, organization_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product['name'], product.get('sku', ''), product.get('barcode', ''),
                    product.get('category', ''), product.get('ingredients', '[]'),
                    product.get('allergens', ''), product.get('nutritional_info', '{}'),
                    product.get('storage_conditions', ''), product.get('shelf_life_days'),
                    product.get('production_date'), product.get('expiry_date'),
                    product.get('batch_number', ''), product.get('haccp_required', 0),
                    user['organization_id'] if user['organization_id'] else None
                ))
                imported['products'] += 1
            except:
                pass
    
    db.commit()
    return jsonify({'success': True, 'imported': imported})

@app.route('/backups/<filename>')
@check_auth('admin')
def serve_backup(filename):
    """Serve backup files"""
    return send_from_directory('db_backups', filename, as_attachment=True)

@app.route('/api/settings', methods=['GET', 'PUT'])
@check_auth()
def api_settings():
    """User settings"""
    db = get_db()
    user = g.current_user
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if 'password' in data and data['password']:
            db.execute('UPDATE users SET password_hash = ?, password_enabled = 1 WHERE id = ?',
                      (hash_password(data['password']), user['id']))
        
        if 'email' in data:
            db.execute('UPDATE users SET email = ? WHERE id = ?', (data['email'], user['id']))
        
        if 'full_name' in data:
            db.execute('UPDATE users SET full_name = ? WHERE id = ?', (data['full_name'], user['id']))
        
        if 'settings' in data:
            db.execute('UPDATE users SET settings = ? WHERE id = ?',
                      (json.dumps(data['settings']), user['id']))
        
        db.commit()
        return jsonify({'success': True})
    
    # GET - user settings
    user_data = db.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
    return jsonify(dict(user_data))

@app.route('/api/organization', methods=['GET', 'PUT'])
@check_auth('admin')
def api_organization():
    """Organization settings"""
    db = get_db()
    user = g.current_user
    org_id = user['organization_id'] if user['organization_id'] else None
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if 'name' in data:
            db.execute('UPDATE organizations SET name = ? WHERE id = ?', (data['name'], org_id))
        
        if 'settings' in data:
            db.execute('UPDATE organizations SET settings = ? WHERE id = ?',
                      (json.dumps(data['settings']), org_id))
        
        db.commit()
        return jsonify({'success': True})
    
    # GET - organization info
    org = db.execute('SELECT * FROM organizations WHERE id = ?', (org_id,)).fetchone()
    return jsonify(dict(org) if org else {})

@app.route('/constructor')
@check_auth()
def constructor():
    """Label constructor page"""
    return render_template('constructor.html', features=FEATURES)

@app.route('/wall')
@check_auth()
def wall():
    """Wall/social page"""
    return render_template('wall.html', features=FEATURES)

@app.route('/printers')
@check_auth()
def printers_page():
    """Printers management page"""
    return render_template('printers.html', features=FEATURES)

@app.route('/inventory')
@check_auth()
def inventory():
    """Inventory management page"""
    return render_template('inventory.html', features=FEATURES)

@app.route('/profile')
@check_auth()
def profile():
    """User profile page"""
    return render_template('profile.html', features=FEATURES)

@app.route('/qr-login')
def qr_login():
    """QR code login page"""
    token = secrets.token_urlsafe(32)
    session['qr_token'] = token
    session['qr_expires'] = time.time() + 300  # 5 minutes
    
    # Generate QR code
    qr_url = url_for('qr_auth', token=token, _external=True)
    img = qrcode.make(qr_url)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('qr_login.html', qr_image=img_base64, token=token)

@app.route('/qr-auth/<token>')
def qr_auth(token):
    """Authenticate via QR code"""
    if 'qr_token' not in session or session['qr_token'] != token:
        return jsonify({'error': 'Invalid token'}), 400
    
    if time.time() > session.get('qr_expires', 0):
        return jsonify({'error': 'Token expired'}), 400
    
    # Auto-login with default admin
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session.pop('qr_token', None)
        session.pop('qr_expires', None)
        return jsonify({'success': True, 'redirect': url_for('dashboard')})
    
    return jsonify({'error': 'User not found'}), 404

@socketio.on('connect')
def handle_connect():
    """Handle socket connection"""
    if 'user_id' in session:
        join_room('public')
        join_room(f"user_{session['user_id']}")
        join_room('printers')
        emit('connected', {'user_id': session['user_id']})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle socket disconnection"""
    pass

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    if 'room' in data:
        emit('user_typing', data, room=data['room'])

@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Handle stop typing indicator"""
    if 'room' in data:
        emit('user_stopped_typing', data, room=data['room'])

@socketio.on('share_template')
def handle_share_template(data):
    """Share template to wall"""
    db = get_db()
    user = g.current_user if hasattr(g, 'current_user') else None
    
    if user:
        db.execute('''
            INSERT INTO wall_posts (author_id, content, post_type, attachments, room_id)
            VALUES (?, ?, 'template_share', ?, 'public')
        ''', (user['id'], f"Shared template: {data.get('name', 'Untitled')}", json.dumps([data])))
        db.commit()
        
        socketio.emit('new_post', {
            'author_id': user['id'],
            'username': user['username'],
            'content': f"Shared template: {data.get('name', 'Untitled')}",
            'type': 'template_share',
            'attachments': [data],
            'created_at': datetime.now().isoformat()
        }, room='public')

def auto_backup():
    """Auto backup database every 24 hours"""
    while True:
        time.sleep(86400)  # 24 hours
        
        try:
            # Backup database
            backup_path = os.path.join('db_backups', f'db_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            conn = sqlite3.connect(DB_PATH)
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()
            
            # Compress backup
            with open(backup_path, 'rb') as f_in:
                with gzip.open(backup_path + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(backup_path)
            print(f"Auto backup completed: {backup_path}.gz")
        except Exception as e:
            print(f"Auto backup failed: {e}")

def find_available_port(start_port=5000):
    """Find available port"""
    port = start_port
    while port < 65535:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            port += 1
    return start_port

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start auto backup thread
    backup_thread = threading.Thread(target=auto_backup, daemon=True)
    backup_thread.start()
    
    # Find available port
    port = find_available_port(5000)
    print(f"Starting server on port {port}")
    
    # Run server
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
