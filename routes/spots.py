from __future__ import annotations

from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_babel import gettext as _

import models.popular_spot as PopularSpotModel
import models.review as ReviewModel
import models.spot as SpotModel
from routes import admin_required
from services.tour_api import (
    ARRANGE_LATEST,
    fetch_detail_common,
    fetch_detail_images,
    fetch_detail_intro,
    fetch_nearby,
    fetch_spots,
)

spots_bp = Blueprint('spots', __name__)


def _type_labels() -> dict[str, str]:
    """Localized content-type labels for the public Tour API."""
    return {
        '12': _('Attraction'), '14': _('Cultural facility'), '15': _('Festival/Performance'),
        '25': _('Travel course'), '28': _('Leisure sports'), '32': _('Lodging'),
        '38': _('Shopping'), '39': _('Restaurant'),
    }


@spots_bp.route('/')
def list_spots():
    """Spot list: latest from the public API, popular from MongoDB."""
    sort = request.args.get('sort', 'latest')
    page = int(request.args.get('page', 1))

    if sort == 'popular':
        result = PopularSpotModel.get_all_popular(page=page, per_page=12)
        for item in result['spots']:
            item.setdefault('date_str', '')
            item.setdefault('mod_str', '')
    else:
        result = fetch_spots(page=page, per_page=12, arrange=ARRANGE_LATEST)
        for item in result['spots']:
            ct = item.get('createdtime', '')
            item['date_str'] = f"{ct[:4]}.{ct[4:6]}.{ct[6:8]}" if len(ct) >= 8 else ''
            mt = item.get('modifiedtime', '')
            item['mod_str'] = f"{mt[:4]}.{mt[4:6]}.{mt[6:8]}" if len(mt) >= 8 else ''

    response = make_response(render_template(
        'spots/list.html', result=result, current_sort=sort,
    ))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response


@spots_bp.route('/api/<content_id>')
def api_detail(content_id):
    """Public API based spot detail page."""
    common = fetch_detail_common(content_id)
    if not common:
        flash(_('Could not load the tourism information.'), 'danger')
        return redirect(url_for('spots.list_spots'))

    content_type_id = common.get('contenttypeid', '12')
    intro = fetch_detail_intro(content_id, content_type_id)
    images = fetch_detail_images(content_id)

    nearby_spots = []
    nearby_restaurants = []
    if common.get('mapx') and common.get('mapy'):
        nearby_spots = fetch_nearby(
            mapx=common['mapx'], mapy=common['mapy'], content_type_id='12',
            radius=5000, count=3, exclude_content_id=content_id,
        )
        nearby_restaurants = fetch_nearby(
            mapx=common['mapx'], mapy=common['mapy'], content_type_id='39',
            radius=5000, count=3, exclude_content_id=content_id,
        )

    popular_info = PopularSpotModel.get_popular_by_contentid(content_id)
    labels = _type_labels()

    return render_template(
        'spots/api_detail.html',
        common=common, intro=intro, images=images,
        type_label=labels.get(content_type_id, _('Tourism')),
        content_type_id=content_type_id,
        nearby_spots=nearby_spots, nearby_restaurants=nearby_restaurants,
        popular_info=popular_info,
    )


@spots_bp.route('/<spot_id>')
def detail(spot_id):
    """DB based spot detail page with reviews."""
    spot = SpotModel.get_spot_by_id(spot_id)
    if not spot:
        flash(_('That spot does not exist.'), 'danger')
        return redirect(url_for('spots.list_spots'))

    reviews = ReviewModel.get_reviews_by_spot(spot_id)
    already_reviewed = False
    if 'user_id' in session:
        already_reviewed = ReviewModel.user_already_reviewed(spot_id, session['user_id'])

    return render_template('spots/detail.html', spot=spot, reviews=reviews,
                           already_reviewed=already_reviewed)


@spots_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    """Create a spot (admin only)."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '')
        region = request.form.get('region', '')
        description = request.form.get('description', '').strip()
        address = request.form.get('address', '').strip()
        image_url = request.form.get('image_url', '').strip()

        errors = []
        if not name:
            errors.append(_('Please enter the spot name.'))
        if not category:
            errors.append(_('Please choose a category.'))
        if not region:
            errors.append(_('Please choose a region.'))
        if not description:
            errors.append(_('Please enter a description.'))

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('spots/create.html',
                                   categories=SpotModel.CATEGORIES,
                                   regions=SpotModel.REGIONS, form=request.form)

        spot_id = SpotModel.create_spot(
            name=name, category=category, region=region, description=description,
            address=address, image_url=image_url, created_by=session['user_id'],
        )
        flash(_('Spot "%(name)s" has been registered.', name=name), 'success')
        return redirect(url_for('spots.detail', spot_id=spot_id))

    return render_template('spots/create.html', categories=SpotModel.CATEGORIES,
                           regions=SpotModel.REGIONS)


@spots_bp.route('/<spot_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(spot_id):
    """Edit a spot (admin only)."""
    spot = SpotModel.get_spot_by_id(spot_id)
    if not spot:
        flash(_('That spot does not exist.'), 'danger')
        return redirect(url_for('spots.list_spots'))

    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'category': request.form.get('category', ''),
            'region': request.form.get('region', ''),
            'description': request.form.get('description', '').strip(),
            'address': request.form.get('address', '').strip(),
            'image_url': request.form.get('image_url', '').strip(),
        }

        errors = []
        if not data['name']:
            errors.append(_('Please enter the spot name.'))
        if not data['category']:
            errors.append(_('Please choose a category.'))

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('spots/edit.html', spot=spot,
                                   categories=SpotModel.CATEGORIES,
                                   regions=SpotModel.REGIONS)

        SpotModel.update_spot(spot_id, data)
        flash(_('The spot information has been updated.'), 'success')
        return redirect(url_for('spots.detail', spot_id=spot_id))

    return render_template('spots/edit.html', spot=spot,
                           categories=SpotModel.CATEGORIES, regions=SpotModel.REGIONS)


@spots_bp.route('/<spot_id>/delete', methods=['POST'])
@admin_required
def delete(spot_id):
    """Delete a spot (admin only)."""
    spot = SpotModel.get_spot_by_id(spot_id)
    if not spot:
        flash(_('That spot does not exist.'), 'danger')
        return redirect(url_for('spots.list_spots'))

    SpotModel.delete_spot(spot_id)
    flash(_('Spot "%(name)s" has been deleted.', name=spot['name']), 'success')
    return redirect(url_for('spots.list_spots'))
