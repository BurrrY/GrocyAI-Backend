import json

from pygrocy.data_models.product import Product
from rapidfuzz import process
import os
from pygrocy import Grocy, TransactionType
from rapidfuzz import fuzz

grocy = Grocy("http://192.168.178.13", os.environ.get("GROCY_API_KEY"), port = 9283)

def combined_score(c_query: str, target: str, *, score_cutoff=None, **kwargs) -> float:
    return (
        0.5 * fuzz.ratio(c_query, target) +
        0.3 * fuzz.partial_ratio(c_query, target) +
        0.2 * fuzz.token_sort_ratio(c_query, target)
    )


def set_amount_per_name(product_name, amount):
    found_product = get_prod_from_stock(product_name)
    print("Found Product: ", str(found_product))

    if isinstance(found_product, Product):
        print(found_product)
        grocy.inventory_product(new_amount=amount, product_id=found_product.id)
        return {
            "name": found_product.name,
            "old_amount": found_product.available_amount,
            "new_amount": amount,
            "unit_singular": found_product.default_quantity_unit_purchase.name,
            "unit_plural": found_product.default_quantity_unit_purchase.name_plural,
        }
    else:
        return {
            "error": "Product not found",
        }

def add_amount_per_name(product_name, amount):
    found_product = get_prod_from_stock(product_name)
    print("Found Product: ", str(found_product))

    if isinstance(found_product, Product):
        print(found_product)
        grocy.add_product(amount=amount, product_id=found_product.id, price=0)
        return {
            "name": found_product.name,
            "new_amount": found_product.available_amount+float(amount),
            "added_amount": amount,
            "unit_singular": found_product.default_quantity_unit_purchase.name,
            "unit_plural": found_product.default_quantity_unit_purchase.name_plural,
        }
    else:
        return {
            "error": "Product not found",
        }

def get_prod_from_stock(product_name):
    print("Searching for ", product_name)

    found_product = None
    all_products=[]
    try:
        all_products = grocy.all_products()
    except Exception as e:
        print(e)

    name_map = {p.name: p for p in all_products}

    best_match = process.extractOne(
        product_name,
        name_map.keys(),
        scorer=combined_score,
    )
    print("Best Match: ", best_match)


    match_name, score, _ = best_match
    found_product = name_map[match_name]

    found_product = grocy.product(found_product.id)
    if found_product is None:
        return {
            "error": "Product not found",
        }
    else:
        return found_product


def consumer_amount_per_name(product_name, amount):
    found_product = get_prod_from_stock(product_name)
    print("Found Product: ", str(found_product))

    if isinstance(found_product, Product):
        print(found_product)
        grocy.consume_product(found_product.id, amount)
        return {
            "name": found_product.name,
            "removed_amount": amount,
            "remaining_amount": found_product.available_amount-float(amount),
            "unit_singular": found_product.default_quantity_unit_purchase.name,
            "unit_plural": found_product.default_quantity_unit_purchase.name_plural,
        }
    else:
        return {
            "error": "Product not found",
        }


def get_amount_per_name(product_name):
    found_product = get_prod_from_stock(product_name)
    print("Found Product: ", str(found_product))

    if isinstance(found_product, Product):
        print(found_product)
        return {
            "name": found_product.name,
            "amount": found_product.available_amount,
            "unit_singular": found_product.default_quantity_unit_purchase.name,
            "unit_plural": found_product.default_quantity_unit_purchase.name_plural,
        }
    else:
        return {
            "error": "Product not found",
        }
