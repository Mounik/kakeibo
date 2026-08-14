from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.categories import bp
from app.categories.forms import CategoryForm, CategoryFilterForm
from app.models import Category, CategoryKindEnum, Expense
from app import db
from sqlalchemy import func


@bp.route('/')
@login_required
def index():
    form = CategoryFilterForm(request.args)
    query = Category.query.filter_by(owner_id=current_user.id)

    if form.kind.data:
        query = query.filter_by(kind=form.kind.data)

    categories = query.order_by(Category.kind, Category.name).all()

    usage = {}
    rows = db.session.query(
        Expense.category_id, func.count(Expense.id), func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.owner_id == current_user.id,
        Expense.category_id.isnot(None),
    ).group_by(Expense.category_id).all()
    for cat_id, count, total in rows:
        usage[cat_id] = {'count': count, 'total': float(total)}

    return render_template(
        'categories/index.html',
        title='Catégories',
        categories=categories,
        form=form,
        usage=usage,
        kinds={k.value: k.name for k in CategoryKindEnum},
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            kind=form.kind.data,
            color=form.color.data,
            icon=form.icon.data,
            owner_id=current_user.id,
        )
        db.session.add(category)
        db.session.commit()
        flash('Catégorie créée.', 'success')
        return redirect(url_for('categories.index'))
    return render_template('categories/form.html', form=form, title='Nouvelle catégorie')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    category = Category.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    if category.is_system:
        flash('Les catégories système ne peuvent pas être modifiées.', 'warning')
        return redirect(url_for('categories.index'))

    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()
        flash('Catégorie mise à jour.', 'success')
        return redirect(url_for('categories.index'))
    return render_template('categories/form.html', form=form, category=category, title='Modifier la catégorie')


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    category = Category.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    if category.is_system:
        flash('Les catégories système ne peuvent pas être supprimées.', 'warning')
        return redirect(url_for('categories.index'))

    if category.expenses.count() > 0:
        flash('Impossible de supprimer : des dépenses utilisent cette catégorie.', 'danger')
        return redirect(url_for('categories.index'))

    db.session.delete(category)
    db.session.commit()
    flash('Catégorie supprimée.', 'success')
    return redirect(url_for('categories.index'))


@bp.route('/api/kinds')
@login_required
def api_kinds():
    return jsonify([{'value': k.value, 'label': k.name} for k in CategoryKindEnum])
