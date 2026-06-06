from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_babel import gettext as _

import models.review as ReviewModel
import models.spot as SpotModel
from extensions.db import mongo
from routes import login_required

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('/')
def index():
    """Public review feed with filters and pagination."""
    page     = request.args.get('page', 1, type=int)
    per_page = 9
    skip     = (page - 1) * per_page

    rating_filter = request.args.get('rating', '', type=str)
    sort_by       = request.args.get('sort', 'latest')

    match_stage = {}
    if rating_filter and rating_filter.isdigit():
        match_stage['rating'] = int(rating_filter)

    sort_stage = {'created_at': -1} if sort_by == 'latest' else {'rating': -1, 'created_at': -1}

    pipeline = [
        {'$match': match_stage},
        {'$sort':  sort_stage},
        {
            '$lookup': {
                'from':         'tourist_spots',
                'localField':   'spot_id',
                'foreignField': '_id',
                'as':           'spot',
            }
        },
        {'$unwind': {'path': '$spot', 'preserveNullAndEmptyArrays': True}},
        {
            '$project': {
                'username':    1,
                'rating':      1,
                'content':     1,
                'created_at':  1,
                'spot_id':     1,
                'spot_name':   {'$ifNull': ['$spot_name', '$spot.name']},
                'spot_region': '$spot.region',
                'spot_image':  '$spot.image_url',
                'spot_cat':    '$spot.category',
            }
        },
        {'$skip':  skip},
        {'$limit': per_page},
    ]

    count_pipeline = [
        {'$match': match_stage},
        {'$count': 'total'},
    ]
    count_result = list(mongo.db.reviews.aggregate(count_pipeline))
    total        = count_result[0]['total'] if count_result else 0
    total_pages  = max(1, (total + per_page - 1) // per_page)

    entries = list(mongo.db.reviews.aggregate(pipeline))

    stats_pipeline = [
        {
            '$group': {
                '_id':        None,
                'avg_rating': {'$avg': '$rating'},
                'count':      {'$sum': 1},
            }
        }
    ]
    stats_result = list(mongo.db.reviews.aggregate(stats_pipeline))
    _avg = stats_result[0]['avg_rating'] if stats_result else None
    stats = {
        'avg_rating': round(_avg, 1) if _avg is not None else 0,
        'count':      stats_result[0]['count'] if stats_result else 0,
    }

    dist_pipeline = [
        {'$group': {'_id': '$rating', 'cnt': {'$sum': 1}}},
        {'$sort':  {'_id': -1}},
    ]
    dist_raw  = {d['_id']: d['cnt'] for d in mongo.db.reviews.aggregate(dist_pipeline)}
    dist      = {r: dist_raw.get(r, 0) for r in range(5, 0, -1)}

    return render_template(
        'reviews/index.html',
        entries=entries,
        stats=stats,
        dist=dist,
        page=page,
        total_pages=total_pages,
        total=total,
        rating_filter=rating_filter,
        sort_by=sort_by,
    )


@reviews_bp.route('/write', methods=['GET'])
@login_required
def write_page():
    """Standalone review form with free-text spot name."""
    return render_template('reviews/write.html')


@reviews_bp.route('/write', methods=['POST'])
@login_required
def write_free():
    """Persist a free-text spot review."""
    spot_name = request.form.get('spot_name', '').strip()
    rating    = request.form.get('rating', '').strip()
    content   = request.form.get('content', '').strip()

    errors = []
    if not spot_name:
        errors.append(_('Please enter the spot name.'))
    if not rating or not rating.isdigit() or not (1 <= int(rating) <= 5):
        errors.append(_('Please choose a rating between 1 and 5 stars.'))
    if not content or len(content) < 5:
        errors.append(_('Please enter at least 5 characters.'))

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('reviews.write_page'))

    ReviewModel.create_free_review(
        spot_name=spot_name,
        user_id=session['user_id'],
        username=session['username'],
        rating=int(rating),
        content=content,
    )
    flash(_('Your review has been posted!'), 'success')
    return redirect(url_for('reviews.index'))


@reviews_bp.route('/spots/<spot_id>/write', methods=['POST'])
@login_required
def write(spot_id):
    """Handle review submission from a spot detail page."""
    spot = SpotModel.get_spot_by_id(spot_id)
    if not spot:
        flash(_('That spot does not exist.'), 'danger')
        return redirect(url_for('spots.list_spots'))

    if ReviewModel.user_already_reviewed(spot_id, session['user_id']):
        flash(_('You have already written a review.'), 'warning')
        return redirect(url_for('spots.detail', spot_id=spot_id))

    rating  = request.form.get('rating', '')
    content = request.form.get('content', '').strip()

    errors = []
    if not rating or not rating.isdigit() or not (1 <= int(rating) <= 5):
        errors.append(_('Please choose a rating between 1 and 5 stars.'))
    if not content or len(content) < 5:
        errors.append(_('Please enter at least 5 characters for your review.'))

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('spots.detail', spot_id=spot_id))

    ReviewModel.create_review(
        spot_id=spot_id,
        user_id=session['user_id'],
        username=session['username'],
        rating=int(rating),
        content=content
    )
    SpotModel.recalculate_rating(spot_id)
    flash(_('Your review has been posted.'), 'success')
    return redirect(url_for('spots.detail', spot_id=spot_id))


@reviews_bp.route('/<review_id>/delete', methods=['POST'])
@login_required
def delete(review_id):
    """Delete a review (author or admin only)."""
    review = ReviewModel.get_review_by_id(review_id)
    if not review:
        flash(_('That review does not exist.'), 'danger')
        return redirect(url_for('main.index'))

    is_owner = str(review['user_id']) == session['user_id']
    is_admin = session.get('role') == 'admin'

    if not is_owner and not is_admin:
        flash(_('You do not have permission to delete this.'), 'danger')
        return redirect(url_for('reviews.index'))

    spot_id = review.get('spot_id')
    ReviewModel.delete_review(review_id)
    if spot_id:
        SpotModel.recalculate_rating(str(spot_id))
    flash(_('The review has been deleted.'), 'success')

    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('reviews.index'))
