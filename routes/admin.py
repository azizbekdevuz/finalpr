from bson import ObjectId, json_util
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import gettext as _

from extensions.db import mongo
from routes import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/db')
@admin_required
def db_manage():
    """DB의 모든 컬렉션과 문서를 조회하는 관리자 페이지."""
    # 현재 DB의 모든 컬렉션 이름 가져오기
    collections = mongo.db.list_collection_names()
    collections.sort()

    # 기본 선택 컬렉션: 쿼리 파라미터가 없으면 'users' 등 기본값
    selected_col = request.args.get('col', collections[0] if collections else None)

    documents = []
    if selected_col and selected_col in collections:
        # 최근 추가된 순서로 100개까지만 표시
        cursor = mongo.db[selected_col].find().sort('_id', -1).limit(100)

        for doc in cursor:
            # 표시하기 좋게 _id는 문자열로, 나머지는 포맷팅
            doc_id = str(doc.get('_id', ''))
            # 전체 문서를 보기 좋게 JSON 문자열로 변환 (미리보기에 사용)
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
    """지정된 컬렉션의 문서를 강제 삭제합니다."""
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
    """지정된 문서를 JSON 형태로 직접 수정합니다."""
    if request.method == 'POST':
        json_data = request.form.get('json_data', '')
        try:
            # 입력받은 JSON 문자열을 딕셔너리로 파싱
            parsed_data = json_util.loads(json_data)

            # _id는 수정하지 않도록 안전장치
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
            # 오류 발생 시 다시 에디터 페이지를 보여줌
            return redirect(url_for('admin.db_edit', collection=collection, doc_id=doc_id))

    # GET 요청: 문서 불러오기
    try:
        doc = mongo.db[collection].find_one({'_id': ObjectId(doc_id)})
        if not doc:
            flash(_('Document not found.'), 'danger')
            return redirect(url_for('admin.db_manage', col=collection))

        # JSON 문자열로 변환하여 textarea에 표시 (들여쓰기 적용)
        json_str = json_util.dumps(doc, ensure_ascii=False, indent=4)
        return render_template('admin/db_edit.html',
                               collection=collection,
                               doc_id=doc_id,
                               json_str=json_str)
    except Exception as e:
        flash(_('An error occurred while loading the document: %(error)s',
                error=str(e)), 'danger')
        return redirect(url_for('admin.db_manage', col=collection))
