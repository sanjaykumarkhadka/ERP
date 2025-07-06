from flask import Blueprint, render_template, request, redirect, url_for, flash

injected_products_bp = Blueprint('injected_products', __name__, template_folder='templates')

# Injected Products List Route
@injected_products_bp.route('/injected_products_list', methods=['GET'])
def injected_products_list():
    from app import db
    from models.injected_products import InjectedProducts
    products = InjectedProducts.query.all()
    return render_template('injected_products/list.html', products=products)

# Injected Products Create Route
@injected_products_bp.route('/injected_products_create', methods=['GET', 'POST'])
def injected_products_create():
    from app import db
    from models.injected_products import InjectedProducts
    from models.production_plan import FinishedGoods

    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        injection_rate = float(request.form['injection_rate'])

        new_product = InjectedProducts(
            product_id=product_id,
            injection_rate=injection_rate
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Injected Product created successfully!", "success")
        return redirect(url_for('injected_products.injected_products_list'))

    finished_goods = FinishedGoods.query.all()
    return render_template('injected_products/create.html', finished_goods=finished_goods)