from bson import ObjectId, json_util
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import gettext as _

from extensions.db import mongo
from routes import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/db')
@admin_required
def db_manage():
    """List collections and preview documents (admin)."""
    collections = mongo.db.list_collection_names()
    collections.sort()

    selected_col = request.args.get('col', collections[0] if collections else None)

    documents = []
    if selected_col and selected_col in collections:
        cursor = mongo.db[selected_col].find().sort('_id', -1).limit(100)

        for doc in cursor:
            doc_id = str(doc.get('_id', ''))
            json_str = json_util.dumps(doc, ensure_ascii=False)
            documents.append({
                '_id': doc_id,
                'raw': doc,
                'json_str': json_str
            })

    return render_template('admin/db_manage.html',
                           collections=collections,
                           selected_col=selected_col,
                           documents=documents)


@admin_bp.route('/db/delete/<collection>/<doc_id>', methods=['POST'])
@admin_required
def db_delete(collection, doc_id):
    """Delete one document from a collection."""
    try:
        result = mongo.db[collection].delete_one({'_id': ObjectId(doc_id)})
        if result.deleted_count > 0:
            flash(_('Data was deleted from the %(collection)s collection.',
                    collection=collection), 'success')
        else:
            flash(_('Could not find the document to delete.'), 'warning')
    except Exception as e:
        flash(_('An error occurred while deleting: %(error)s', error=str(e)), 'danger')

    return redirect(url_for('admin.db_manage', col=collection))


@admin_bp.route('/db/edit/<collection>/<doc_id>', methods=['GET', 'POST'])
@admin_required
def db_edit(collection, doc_id):
    """Edit a document as raw JSON."""
    if request.method == 'POST':
        json_data = request.form.get('json_data', '')
        try:
            parsed_data = json_util.loads(json_data)

            # Never overwrite _id from editor input. / 편집기 입력으로 _id를 덮어쓰지 않습니다.
            if '_id' in parsed_data:
                del parsed_data['_id']

            mongo.db[collection].update_one(
                {'_id': ObjectId(doc_id)},
                {'$set': parsed_data}
            )
            flash(_('The data was updated successfully.'), 'success')
            return redirect(url_for('admin.db_manage', col=collection))
        except Exception as e:
            flash(_('An error occurred while parsing or saving JSON: %(error)s',
                    error=str(e)), 'danger')
            return redirect(url_for('admin.db_edit', collection=collection, doc_id=doc_id))

    try:
        doc = mongo.db[collection].find_one({'_id': ObjectId(doc_id)})
        if not doc:
            flash(_('Document not found.'), 'danger')
            return redirect(url_for('admin.db_manage', col=collection))

        json_str = json_util.dumps(doc, ensure_ascii=False, indent=4)
        return render_template('admin/db_edit.html',
                               collection=collection,
                               doc_id=doc_id,
                               json_str=json_str)
    except Exception as e:
        flash(_('An error occurred while loading the document: %(error)s',
                error=str(e)), 'danger')
        return redirect(url_for('admin.db_manage', col=collection))
