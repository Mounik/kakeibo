from flask import render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.notifications import bp
from app.models import Notification
from app import db


@bp.route('/')
@login_required
def index():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).limit(100).all()
    unread = sum(1 for n in notifications if not n.is_read)
    return render_template(
        'notifications/index.html',
        title='Notifications',
        notifications=notifications,
        unread=unread,
    )


@bp.route('/<int:id>/read', methods=['POST'])
@login_required
def mark_read(id):
    notification = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    notification.mark_read()
    return redirect(url_for('notifications.index'))


@bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('Toutes les notifications marquées comme lues.', 'success')
    return redirect(url_for('notifications.index'))


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    notification = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(notification)
    db.session.commit()
    flash('Notification supprimée.', 'success')
    return redirect(url_for('notifications.index'))


@bp.route('/api/unread-count')
@login_required
def api_unread_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})
