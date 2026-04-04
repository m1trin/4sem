from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import db, Visit_logs, User
from app.decorators import check_rights
import csv
import io


bp_reports = Blueprint('reports', __name__, url_prefix='/visit_logs')

@bp_reports.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if current_user.role and current_user.role.name == 'Администратор':
        log_query = Visit_logs.query
    else:
        log_query = Visit_logs.query.filter_by(user_id=current_user.id)

    pagination = log_query.order_by(Visit_logs.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    logs = pagination.items

    return render_template('visit_logs.html', logs=logs, pagination=pagination)


@bp_reports.route('/pages_report')
@login_required
# @check_rights('Администратор')
def pages_report():
    if current_user.role and current_user.role.name == 'Администратор':
        stats = db.session.query(
            Visit_logs.path,
            func.count(Visit_logs.id).label('visit_count')
        ).group_by(Visit_logs.path).order_by(func.count(Visit_logs.id).desc()).all()
    else:
        stats = db.session.query(
            Visit_logs.path,
            func.count(Visit_logs.id).label('visit_count')
        ).filter_by(user_id=current_user.id).group_by(Visit_logs.path).order_by(func.count(Visit_logs.id).desc()).all()
    
    stats_list = []
    for row in stats:
        stats_list.append({
            'path': row[0] if row[0] else '/',
            'count': row[1] if len(row) > 1 else 0
        })
    
    return render_template('pages_report.html', stats=stats_list)


@bp_reports.route('/pages_report/export')
@login_required
@check_rights('Администратор')
def export_pages_report():
    stats = db.session.query(
        Visit_logs.path,
        func.count(Visit_logs.id).label('visit_count')
    ).group_by(Visit_logs.path).order_by(func.count(Visit_logs.id).desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Страница', 'Количество посещений'])

    for idx, row in enumerate(stats, 1):
        path = row[0] if row[0] else '/'
        count = row[1] if len(row) > 1 else 0
        writer.writerow([idx, path, count])

    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=pages_report.csv'}
    )


@bp_reports.route('/users_report')
@login_required
@check_rights('Администратор')
def users_report():
    stats = db.session.query(
        User.id,
        User.last_name,
        User.first_name,
        User.middle_name,
        func.count(Visit_logs.id).label('visit_count')
    ).outerjoin(Visit_logs, User.id == Visit_logs.user_id).group_by(
        User.id, User.last_name, User.first_name, User.middle_name
    ).order_by(func.count(Visit_logs.id).desc()).all()
    
    stats_list = []
    for row in stats:
        stats_list.append({
            'user_id': row[0],
            'last_name': row[1] or '',
            'first_name': row[2] or '',
            'middle_name': row[3] or '',
            'count': row[4] if len(row) > 4 else 0
        })
    
    return render_template('users_report.html', stats=stats_list)


@bp_reports.route('/users_report/export')
@login_required
@check_rights('Администратор')
def export_users_report():
    stats = db.session.query(
        User.id,
        User.last_name,
        User.first_name,
        User.middle_name,
        func.count(Visit_logs.id).label('visit_count')
    ).outerjoin(Visit_logs, User.id == Visit_logs.user_id).group_by(
        User.id, User.last_name, User.first_name, User.middle_name
    ).order_by(func.count(Visit_logs.id).desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Пользователь', 'Количество посещений'])

    for idx, row in enumerate(stats, 1):
        user_id = row[0]
        last_name = row[1] or ''
        first_name = row[2] or ''
        middle_name = row[3] or ''
        count = row[4] if len(row) > 4 else 0
        
        if user_id:
            full_name = f"{last_name} {first_name} {middle_name}".strip()
        else:
            full_name = 'Неаутентифицированный пользователь'
            
        writer.writerow([idx, full_name, count])

    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users_report.csv'}
    )